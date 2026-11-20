"""ANALYSE: the tables Kwame's questions need, for all years and for 2000 onward.

The grain of each table:
  kpis                    one row per window per group (franchise / standalone)
  sensitivity             one row per rule combination per window per metric
  franchise_candidates    one row per collection on the list
  standalone_candidates   one row per standalone film with a usable return
  talent_directors/leads  one row per person with enough usable films

This module produces EVIDENCE. Choosing the shortlist, giving each pick a reason and
interpreting the talent numbers are the analyst's job (docs/memo.md).
"""
from itertools import product

import pandas as pd

from pipeline import config
from pipeline.transform import prepare


def window(fact: pd.DataFrame, start_year: int = None) -> pd.DataFrame:
    """All years (None) or start_year onward. A film with no date stays in "all years" only."""
    if start_year is None:
        return fact
    return fact[fact["release_year"].ge(start_year).fillna(False)]


def hit_rate(roi: pd.Series) -> float:
    """Share of films with a usable return that earned at least HIT_ROI times their budget."""
    return (roi >= config.HIT_ROI).sum() / max(roi.count(), 1)


def kpi_table(fact: pd.DataFrame, start_year: int = None) -> pd.DataFrame:
    """One row per group. Two ways to measure return, with the group sizes beside them:

      median_roi       the typical film: every film counts equally
      ratio_of_totals  total revenue / total budget: big-budget films count more
    """
    films = window(fact, start_year)
    table = films.groupby("group").agg(
        titles=("movie_id", "size"),            # size counts rows, including films with no return
        usable=("roi", "count"),                # count skips NaN: films with a usable return
        median_roi=("roi", "median"),
        mean_roi=("roi", "mean"),
        hit_rate=("roi", hit_rate),
        median_revenue_m=("revenue_clean", lambda s: s.median() / 1e6),
    )
    usable = films[films["roi"].notna()]
    totals = usable.groupby("group")[["revenue_clean", "budget_clean"]].sum()
    table["ratio_of_totals"] = totals["revenue_clean"] / totals["budget_clean"]

    table = table.reindex(["franchise", "standalone"])      # both groups always shown, even if empty
    table["small_group"] = table["usable"].fillna(0) < config.MIN_GROUP_SIZE
    table.insert(0, "window", "all years" if start_year is None else f"{start_year} onward")
    return table.round(3).rename_axis("group").reset_index()


def both_windows(fact: pd.DataFrame) -> pd.DataFrame:
    return pd.concat([kpi_table(fact), kpi_table(fact, config.WINDOW_START_YEAR)], ignore_index=True)


def leader(kpis: pd.DataFrame, metric: str) -> str:
    values = kpis.set_index("group")[metric]
    if values.isna().any():
        return "undetermined"
    return "franchise" if values["franchise"] > values["standalone"] else "standalone"


# ------------------------------------------------------------- does a decision change the answer?
SENSITIVITY_RULES = {
    "zero_revenue_is_unknown": [True, False],
    "tiny_money_is_unknown": [True, False],
    "franchise_min_on_list": [1, 2],
    "released_only": [True, False],
}


def sensitivity(films: pd.DataFrame) -> pd.DataFrame:
    """Rerun the whole comparison under every combination of the contested rules
    (2 x 2 x 2 x 2 = 16), for both windows and both metrics. If the leader ever
    changes, the memo must say so."""
    rows = []
    for values in product(*SENSITIVITY_RULES.values()):
        changed = dict(zip(SENSITIVITY_RULES, values))
        rules = {**config.RULES, **changed}
        fact, _ = prepare(films, rules)
        for start in (None, config.WINDOW_START_YEAR):
            kpis = kpi_table(fact, start)
            by_group = kpis.set_index("group")
            for metric in ("median_roi", "ratio_of_totals"):
                rows.append({
                    **changed,
                    "window": kpis["window"].iloc[0],
                    "metric": metric,
                    "franchise": by_group.loc["franchise", metric],
                    "standalone": by_group.loc["standalone", metric],
                    "n_franchise": by_group.loc["franchise", "usable"],
                    "n_standalone": by_group.loc["standalone", "usable"],
                    "leader": leader(kpis, metric),
                    "current_rules": rules == config.RULES,
                })
    out = pd.DataFrame(rows)
    out["gap"] = (out["franchise"] - out["standalone"]).round(3)
    return out


def flips(sens: pd.DataFrame) -> pd.DataFrame:
    """For each window and metric: how many different leaders the rule choices produce."""
    return (sens.groupby(["window", "metric"])["leader"]
                .agg(leaders="nunique", values=lambda s: ", ".join(sorted(set(s))))
                .reset_index())


# ------------------------------------------------------------- raw material for the shortlist
def franchise_candidates(fact: pd.DataFrame) -> pd.DataFrame:
    """One row per collection, with what a bundle negotiation needs, including its weakest film."""
    typical = fact["roi"].median()                       # a typical title on the whole list
    table = (fact[fact["group"].eq("franchise")]
             .groupby(["collection_id", "collection_name"])
             .agg(films_on_list=("movie_id", "size"),
                  usable=("roi", "count"),
                  median_roi=("roi", "median"),
                  weakest_roi=("roi", "min"),
                  best_roi=("roi", "max"),
                  share_recouped=("roi", lambda s: (s >= 1).sum() / max(s.count(), 1)),
                  total_budget_m=("budget_clean", lambda s: s.sum() / 1e6),
                  total_revenue_m=("revenue_clean", lambda s: s.sum() / 1e6),
                  first_year=("release_year", "min"),
                  last_year=("release_year", "max"),
                  titles=("title", " | ".join))
             .reset_index())
    table["pooled_roi"] = table["total_revenue_m"] / table["total_budget_m"].where(table["total_budget_m"] > 0)
    table["vs_typical_title"] = table["median_roi"] / typical          # 1.0 = like a typical title
    table["all_before_window"] = table["last_year"].lt(config.WINDOW_START_YEAR).fillna(False)
    return table.sort_values(["usable", "median_roi"], ascending=False).round(3).reset_index(drop=True)


def standalone_candidates(fact: pd.DataFrame) -> pd.DataFrame:
    films = fact[fact["group"].eq("standalone") & fact["roi"].notna()]
    table = films[["movie_id", "title", "release_year", "roi", "budget_clean", "revenue_clean",
                   "vote_count", "vote_average", "genres"]].assign(
        enough_votes=films["vote_count"].ge(config.STANDALONE_MIN_VOTES).fillna(False),
        before_window=films["release_year"].lt(config.WINDOW_START_YEAR).fillna(False),
        vs_typical_title=films["roi"] / fact["roi"].median(),
    )
    return table.sort_values("roi", ascending=False).round(3).reset_index(drop=True)


# ------------------------------------------------------------- talent
def talent_table(people: pd.DataFrame, fact: pd.DataFrame, role: str) -> pd.DataFrame:
    """people has one row per film per person, so people -> film is many_to_one."""
    joined = people.merge(fact[["movie_id", "roi", "group", "release_year"]], on="movie_id",
                          how="inner", validate="many_to_one")       # people on excluded films drop out
    table = (joined.groupby(["person_id", "name"])
                   .agg(films_on_list=("movie_id", "nunique"),
                        usable=("roi", "count"),
                        median_roi=("roi", "median"),
                        hit_rate=("roi", hit_rate),
                        franchise_films=("group", lambda s: (s == "franchise").sum()),
                        latest_year=("release_year", "max"))
                   .reset_index())
    table = table[table["usable"] >= config.TALENT_MIN_FILMS]
    table.insert(0, "role", role)
    return table.sort_values(["median_roi", "usable"], ascending=False).round(3).reset_index(drop=True)


def talent(cast: pd.DataFrame, directors: pd.DataFrame, fact: pd.DataFrame):
    leads = cast.loc[cast["order"].le(config.LEAD_CAST_MAX_ORDER), ["movie_id", "person_id", "name"]]
    return (talent_table(directors, fact, "director"),
            talent_table(leads.drop_duplicates(), fact, "lead actor"))
