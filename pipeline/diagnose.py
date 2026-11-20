"""DIAGNOSE: flag everything suspicious in the films and measure what each flag does.

This module FINDS and MEASURES. It does not decide. For each condition it reports how
many films have it, which group they're in, and how far the franchise-vs-standalone
gap moves if those films are left out (gap_shift). Ranking by risk and the verdict on
each finding are written by the analyst in docs/findings.md.

Grain: films_flagged = one row per film; findings = one row per flag.
Return here uses the RAW money (no cleaning rules), so the flags show the data as received.
"""
import numpy as np
import pandas as pd

from pipeline import config
from pipeline.validate import title_year_key


def raw_roi(films: pd.DataFrame) -> pd.Series:
    return (films["revenue"] / films["budget"]).where(films["budget"].gt(0) & films["revenue"].gt(0))


def add_flags(films: pd.DataFrame) -> pd.DataFrame:
    """One True/False column per condition."""
    tiny = config.RULES["tiny_money_threshold"]
    log_roi = np.log10(raw_roi(films))                  # returns are skewed: judge outliers on a log scale
    q1, q3 = log_roi.quantile([0.25, 0.75])
    fence = 1.5 * (q3 - q1)
    return films.assign(
        flag_budget_zero=films["budget"].eq(0),
        flag_revenue_zero=films["revenue"].eq(0),
        flag_budget_tiny=films["budget"].between(1, tiny - 1),
        flag_revenue_tiny=films["revenue"].between(1, tiny - 1),
        flag_not_released=films["status"].ne("Released"),
        flag_no_release_date=films["release_date"].isna(),
        flag_before_2000=films["release_year"].lt(config.WINDOW_START_YEAR).fillna(False),
        flag_short_film=films["runtime"].between(1, config.RULES["short_film_minutes"] - 1),
        flag_no_runtime=films["runtime"].fillna(0).eq(0),
        flag_same_title_and_year=title_year_key(films).duplicated(keep=False),
        flag_return_outlier=((log_roi < q1 - fence) | (log_roi > q3 + fence)).fillna(False),
    )


def is_franchise(films: pd.DataFrame) -> pd.Series:
    """The franchise definition from config (ADR-003), so the diagnosis and the analysis agree."""
    on_list = films.groupby("collection_id")["movie_id"].transform("count")
    return films["collection_id"].notna() & on_list.ge(config.RULES["franchise_min_on_list"]).fillna(False)


def gap(films: pd.DataFrame) -> float:
    """Median franchise return minus median standalone return (raw money)."""
    group = np.where(is_franchise(films), "franchise", "standalone")
    medians = raw_roi(films).groupby(group).median()
    return medians.get("franchise", np.nan) - medians.get("standalone", np.nan)


def findings(flagged: pd.DataFrame) -> pd.DataFrame:
    franchise = is_franchise(flagged)
    gap_all = gap(flagged)
    rows = []
    for column in [c for c in flagged.columns if c.startswith("flag_")]:
        has_it = flagged[column]
        rows.append({
            "flag": column.removeprefix("flag_"),
            "films": int(has_it.sum()),
            "pct": round(100 * has_it.mean(), 1),
            "franchise_films": int((has_it & franchise).sum()),
            "standalone_films": int((has_it & ~franchise).sum()),
            "before_2000": int((has_it & flagged["flag_before_2000"]).sum()),
            "gap_all": round(gap_all, 3),
            "gap_without": round(gap(flagged[~has_it]), 3),
            "example_ids": " ".join(map(str, flagged.loc[has_it, "movie_id"].head(8))),
        })
    table = pd.DataFrame(rows)
    table["gap_shift"] = (table["gap_without"] - table["gap_all"]).round(3)
    return table.sort_values("films", ascending=False).reset_index(drop=True)


def missing_vs_present(flagged: pd.DataFrame) -> pd.DataFrame:
    """Are films with no revenue figure different from the rest? (older? more franchise?)"""
    return (flagged.assign(before_2000=flagged["flag_before_2000"],
                           in_collection=flagged["collection_id"].notna(),
                           has_budget=flagged["budget"].gt(0))
                   .groupby("flag_revenue_zero")[["before_2000", "in_collection", "has_budget"]]
                   .mean().round(2).reset_index())
