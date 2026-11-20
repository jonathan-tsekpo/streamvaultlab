"""QA GATE: reconciliations that must all pass before anything is written.

They follow the brief's own words: every id accounted for, totals reconciling to what
was given, joins proven not to drop or duplicate a film, both groups present so the
comparison is real. If any check fails the run stops and publishes nothing: a partial
answer is worse than no answer.
"""
from pipeline import config


class ReconciliationError(Exception):
    """The outputs don't reconcile to the inputs."""


FINISHED = ["200", "404"]        # every other status means a fetch failed or was skipped
UNUSABLE = ["blank line", "not a TMDb id", "not found on TMDb (404)", "fetch failed", "not fetched (offline)"]


def run_checks(t: dict) -> dict:
    """t holds the tables of one run. Returns {check: passed}."""
    lines, ids, acq, films, fact, account = (t["lines"], t["ids"], t["acquisition"], t["films"],
                                             t["fact_films"], t["id_account"])
    return {
        "every line kept or quarantined": len(lines) == len(ids) + len(t["id_quarantine"]),
        "every usable id fetched exactly once": len(acq) == len(ids) and acq["movie_id"].is_unique,
        "no fetch left unfinished": bool(acq["movie_status"].isin(FINISHED).all()),
        "every fetched film flattened": len(films) == acq["movie_status"].eq("200").sum(),
        "every film in analysis or excluded": len(films) == len(fact) + len(t["film_quarantine"]),
        "one row per film": bool(fact["movie_id"].is_unique),
        "id account has every line": len(account) == len(lines),
        "id account matches the analysis": account["outcome"].eq("in analysis").sum() == len(fact),
        "no negative money": not (fact["budget"].lt(0).any() or fact["revenue"].lt(0).any()),
        "both groups present in both windows": bool(t["kpis"]["titles"].notna().all()),
        "unusable lines under threshold": account["outcome"].isin(UNUSABLE).mean() <= config.MAX_UNUSABLE_SHARE,
    }


def check_before_load(tables: dict) -> dict:
    results = run_checks(tables)
    failed = [name for name, passed in results.items() if not passed]
    if failed:
        raise ReconciliationError(f"checks failed, nothing written: {failed}")
    return results
