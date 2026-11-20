"""Run the StreamVault licensing pipeline from start to finish.

    python run_pipeline.py                  # fetch whatever isn't cached, then analyse
    python run_pipeline.py --offline        # never touch the network: cache only
    python run_pipeline.py --refresh        # ignore the cache and take a new TMDb snapshot
    python run_pipeline.py --quick          # skip the timing and the live spot-check

Stages: extract -> validate -> transform -> analyse -> QA gate -> load, then timing,
the spot-check and out/summary.md. If the QA gate fails, nothing is written. Every
run, passed or failed, adds one line to out/run_log.jsonl.
"""
import argparse
import json
import logging
import sys
import time
import uuid
from datetime import datetime, timezone

import pandas as pd
from dotenv import load_dotenv

from pipeline import config
from pipeline.analysis import flips, leader, run_analysis, sensitivity
from pipeline.checks import check_before_load
from pipeline.diagnose import add_flags, findings, missing_vs_present
from pipeline.extract import fetch_all, read_id_list
from pipeline.load import write_all
from pipeline.report import write_summary
from pipeline.transform import build_tables, id_account, prepare
from pipeline.validate import validate_ids

log = logging.getLogger("pipeline")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run(offline: bool, refresh: bool, quick: bool) -> dict:
    seconds = {}

    def step(name, function, *args, **kwargs):
        """Run one stage and remember how long it took."""
        start = time.perf_counter()
        result = function(*args, **kwargs)
        seconds[name] = round(time.perf_counter() - start, 3)
        return result

    # ---- EXTRACT and VALIDATE the list
    lines = step("read list", read_id_list)
    ids, id_quarantine = step("validate ids", validate_ids, lines)
    log.info("candidate list: %d lines, %d usable ids, %d quarantined %s", len(lines), len(ids),
             len(id_quarantine), id_quarantine["reason"].value_counts().to_dict())

    acquisition = step("fetch", fetch_all, ids["movie_id"].tolist(), refresh=refresh, offline=offline)
    requests_made = acquisition.attrs["requests_made"]
    log.info("fetched: %d live requests; details %s; credits %s", requests_made,
             acquisition["movie_status"].value_counts().to_dict(),
             acquisition["credits_status"].value_counts().to_dict())

    # ---- TRANSFORM
    films, cast, directors = step("flatten", build_tables, acquisition)
    log.info("films %d (one per film), cast %d (one per film per person), directors %d",
             len(films), len(cast), len(directors))
    fact, film_quarantine = step("clean", prepare, films, config.RULES)
    log.info("in the comparison %d, excluded %d %s", len(fact), len(film_quarantine),
             film_quarantine["reason"].value_counts().to_dict())
    account = step("id account", id_account, lines, ids, id_quarantine, acquisition, film_quarantine)

    # ---- ANALYSE
    flagged = step("diagnose", add_flags, films)
    results = step("analyse", run_analysis, fact, cast, directors)
    kpis = results["kpis"]
    sens = step("sensitivity", sensitivity, films)
    tables = {
        "lines": lines, "ids": ids, "id_quarantine": id_quarantine, "acquisition": acquisition,
        "films": films, "cast": cast, "directors": directors, "fact_films": fact,
        "film_quarantine": film_quarantine, "id_account": account,
        "films_flagged": flagged, "findings": findings(flagged),
        "missing_vs_present": missing_vs_present(flagged),
        "sensitivity": sens, "flips": flips(sens),
        **results,
    }

    # ---- QA GATE, then LOAD
    checks = step("qa gate", check_before_load, tables)
    published = {name: df for name, df in tables.items() if name not in ("lines", "ids")}
    written = step("load", write_all, published)

    metric = config.HEADLINE_METRIC
    lead_all = leader(kpis[kpis["window"].eq("all years")], metric)
    lead_recent = leader(kpis[kpis["window"].ne("all years")], metric)
    log.info("leader on %s: all years = %s | %d onward = %s", metric, lead_all,
             config.WINDOW_START_YEAR, lead_recent)
    if lead_all != lead_recent:
        log.warning("THE ANSWER CHANGES BETWEEN THE TWO WINDOWS: the memo must say so")
    for _, row in tables["flips"][tables["flips"]["leaders"] > 1].iterrows():
        log.warning("the leader on %s (%s) depends on the cleaning rules: %s",
                    row["metric"], row["window"], row["values"])

    meta = {}
    # ---- TIMING and SPOT-CHECK (evidence, written after the gate)
    if not quick:
        from pipeline.timing import time_pipeline
        tables["timing"] = step("timing", time_pipeline, films, cast, directors)
        written += write_all({"timing": tables["timing"]})
        log.info("analysis seconds at %s titles: %s", config.TIMING_SIZES, tables["timing"]["total_s"].tolist())
    if not quick and not offline:
        from pipeline.spot_check import spot_check, summary
        tables["spot_check"] = step("spot-check", spot_check, films, fact)
        written += write_all({"spot_check": tables["spot_check"]})
        meta["spot_check_summary"] = summary(tables["spot_check"])
        log.info(meta["spot_check_summary"])

    fetched = pd.to_datetime(acquisition["movie_fetched_at"], utc=True)
    meta.update({
        "lines_in": len(lines),
        "usable_ids": len(ids),
        "in_analysis": len(fact),
        "outcomes": account["outcome"].value_counts().to_dict(),
        "requests_made": requests_made,
        "snapshot_from": f"{fetched.min():%Y-%m-%d}",
        "snapshot_to": f"{fetched.max():%Y-%m-%d}",
        "rules": config.RULES,
        "headline_metric": metric,
        "leader_all_years": lead_all,
        "leader_recent": lead_recent,
        "checks": checks,
        "seconds": seconds,
        "hashes": {w["table"]: w["hash"] for w in written},
    })
    return meta, tables


def record(entry: dict) -> None:
    """Add one JSON line to the run history."""
    config.RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(config.RUN_LOG, "a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, default=str) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--offline", action="store_true", help="use the cache only")
    parser.add_argument("--refresh", action="store_true", help="ignore the cache and fetch again")
    parser.add_argument("--quick", action="store_true", help="skip timing and the spot-check")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")
    load_dotenv()                                     # reads TMDB_API_KEY from .env
    run_id, started = uuid.uuid4().hex[:8], now()
    try:
        meta, tables = run(args.offline, args.refresh, args.quick)
        meta = {"run_id": run_id, "started": started, "finished": now(), "status": "success", **meta}
        record(meta)
        write_summary(meta, tables)
        log.info("done: tables in %s; summary in %s", config.TABLES, config.SUMMARY)
        return 0
    except Exception as error:
        record({"run_id": run_id, "started": started, "finished": now(), "status": "failed",
                "error": f"{type(error).__name__}: {error}"})
        log.error("FAILED: %s: %s", type(error).__name__, error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
