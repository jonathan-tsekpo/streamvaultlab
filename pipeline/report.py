"""REPORT: put the results of a run into one readable file, out/summary.md.

This is what you share for review and what you draw the memo from. It holds only
counts, film titles and figures from TMDb (public data) and our own tables.
It never contains the API key.
"""
import pandas as pd

from pipeline import config


def section(title: str, table: pd.DataFrame, note: str = "", rows: int = None) -> str:
    shown = table if rows is None else table.head(rows)
    body = shown.to_string(index=False) if len(shown) else "(no rows)"
    more = f"\n... {len(table) - rows} more rows in out/tables/" if rows and len(table) > rows else ""
    return f"## {title}\n{note}\n```text\n{body}{more}\n```\n"


def write_summary(meta: dict, t: dict) -> None:
    outcomes = pd.Series(meta["outcomes"], name="lines").rename_axis("outcome").reset_index()
    checks = pd.Series(meta["checks"], name="passed").rename_axis("check").reset_index()
    sens = t["sensitivity"]
    leaders = (sens.groupby(["window", "metric", "leader"]).size()
                   .rename("rule combinations").reset_index())
    current = sens[sens["current_rules"]].drop(columns="current_rules")

    parts = [
        "# StreamVault run summary\n",
        f"- Run: `{meta['run_id']}` finished {meta['finished']}",
        f"- TMDb snapshot: {meta['snapshot_from']} to {meta['snapshot_to']}; "
        f"live requests this run: {meta['requests_made']}",
        f"- Candidate list: {meta['lines_in']} lines, {meta['usable_ids']} usable ids, "
        f"{meta['in_analysis']} films in the comparison",
        f"- Rules: `{meta['rules']}`",
        f"- Headline metric: {meta['headline_metric']}; leader all years = {meta['leader_all_years']}, "
        f"{config.WINDOW_START_YEAR} onward = {meta['leader_recent']}\n",
        section("1. Where every line of the list went", outcomes),
        section("2. Quality checks (QA gate)", checks),
        section("3. Lines quarantined", t["id_quarantine"][["source_line", "raw_value", "reason", "duplicate_of_line"]]),
        section("4. Films excluded from the comparison", t["film_quarantine"]),
        section("5. Franchise vs standalone, both windows", t["kpis"],
                "titles = films in the group; usable = films with a usable return."),
        section("6. Does any cleaning rule change the answer?", leaders,
                "How many of the 16 rule combinations give each leader."),
        section("6b. The comparison under the current rules", current),
        section("7. Diagnosis: every flag and what it does to the gap", t["findings"],
                "gap_shift = how far the franchise-minus-standalone gap moves if these films are left out."),
        section("8. Films with revenue = 0 vs the rest", t["missing_vs_present"]),
        section("9. Franchise candidates", t["franchise_candidates"].drop(columns="titles"), rows=15),
        section("10. Standalone candidates", t["standalone_candidates"], rows=15),
        section("11. Directors", t["talent_directors"], rows=15),
        section("12. Lead actors", t["talent_leads"], rows=15),
    ]
    if "timing" in t:
        parts.append(section("13. Timing (fetching excluded)", t["timing"]))
    if "spot_check" in t:
        parts.append(section("14. Spot-check against live TMDb", t["spot_check"].drop(columns="checked_at"),
                             meta.get("spot_check_summary", "")))

    config.SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    config.SUMMARY.write_text("\n".join(parts), encoding="utf-8")
