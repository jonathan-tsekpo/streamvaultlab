"""SPOT-CHECK: compare a deliberate sample of our output with the live API.

  1. Choose about 10 films in slices: random (fixed seed), the highest and lowest
     returns, films the cleaning changed most, and boundary cases (1999/2000, a
     collection with one film on the list).
  2. Ask TMDb for them LIVE. The cache is neither used for the live value nor overwritten.
  3. Compare three values per field: our table, our cached response, and live:
       ours == live                    -> match
       ours != live but cached == live -> our bug (we broke it after fetching)
       cached != live                  -> the source changed since our snapshot
       live is 404                     -> genuinely missing now
     A definition mismatch can't be found by code: judge it and write it in "notes".
  4. The tolerance comes from config and is fixed before looking.

Grain: one row per sampled film per field.
"""
from datetime import datetime, timezone

import pandas as pd

from pipeline import config
from pipeline.extract import get, make_session, read_cached

FIELDS = ["title", "release_date", "budget", "revenue", "collection_id"]


def choose_sample(fact: pd.DataFrame) -> dict:
    """{movie_id: slice}. A film is only chosen once."""
    chosen = {}

    def add(movie_ids, label, how_many):
        for movie_id in movie_ids:
            if how_many == 0:
                break
            if movie_id not in chosen:
                chosen[movie_id] = label
                how_many -= 1

    by_roi = fact[fact["roi"].notna()].sort_values("roi")
    boundary = (fact["release_year"].isin([config.WINDOW_START_YEAR - 1, config.WINDOW_START_YEAR]).fillna(False)
                | fact["collection_films_on_list"].eq(1).fillna(False))
    add(fact.sample(frac=1, random_state=config.SPOT_CHECK_SEED)["movie_id"], "random", 4)
    add(by_roi["movie_id"][::-1], "highest return", 2)
    add(by_roi["movie_id"], "lowest return", 2)
    add(fact.loc[fact["money_changed"], "movie_id"], "changed by cleaning", 2)
    add(fact.loc[boundary, "movie_id"], "boundary", 2)
    return chosen


def from_json(movie: dict, field: str):
    if field == "collection_id":
        return (movie.get("belongs_to_collection") or {}).get("id")
    if field == "release_date":
        return movie.get("release_date") or None        # TMDb sends "" when unknown
    return movie.get(field)


def from_table(row: pd.Series, field: str):
    value = row[field]
    if pd.isna(value):
        return None
    if field == "release_date":
        return value.strftime("%Y-%m-%d")
    if field in ("budget", "revenue", "collection_id"):
        return int(value)
    return value


def same(a, b, field) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if field in ("budget", "revenue"):
        return abs(a - b) <= config.MONEY_TOLERANCE
    return a == b


def spot_check(films: pd.DataFrame, fact: pd.DataFrame) -> pd.DataFrame:
    ours = films.set_index("movie_id")
    checked_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []
    with make_session() as session:
        for movie_id, slice_name in choose_sample(fact).items():
            response = get(session, "movie", movie_id)
            if response.status_code == 404:
                rows.append({"movie_id": movie_id, "slice": slice_name, "field": "(whole film)",
                             "ours": "present", "cached": "present", "live": "404",
                             "result": "genuinely missing now"})
                continue
            response.raise_for_status()
            live, cached = response.json(), read_cached("movie", movie_id)
            for field in FIELDS:
                our_value = from_table(ours.loc[movie_id], field)
                was, now = from_json(cached, field), from_json(live, field)
                if same(our_value, now, field):
                    result = "match"
                elif same(was, now, field):
                    result = "our bug"
                else:
                    result = "source changed"
                rows.append({"movie_id": movie_id, "slice": slice_name, "field": field,
                             "ours": our_value, "cached": was, "live": now, "result": result})
    report = pd.DataFrame(rows)
    report.insert(0, "checked_at", checked_at)
    report["notes"] = ""                     # for definition mismatches: your judgement
    return report


def summary(report: pd.DataFrame) -> str:
    """The sentences that go above the reconciliation table."""
    films = report["movie_id"].nunique()
    all_match = int(report.groupby("movie_id")["result"].apply(lambda r: r.eq("match").all()).sum())
    problems = report.loc[report["result"].ne("match"), "result"].value_counts().to_dict() or "none"
    slices = ", ".join(sorted(report["slice"].unique()))
    return (f"Checked {films} films live at {report['checked_at'].iloc[0]}, chosen by slice ({slices}); "
            f"money tolerance ${config.MONEY_TOLERANCE}, exact match on other fields. "
            f"{all_match} of {films} matched on every field. Differences: {problems}.")
