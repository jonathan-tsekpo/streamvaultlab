"""TIMING: how long the analysis takes at 127, 500 and 5,000 titles.

What is timed: from the flattened films, cast and directors tables to the finished
comparison, shortlist and talent tables. Fetching is NOT timed: network time depends
on TMDb and the connection, not on the code. It is reported separately as a lower
bound (two calls per film, spaced THROTTLE_SECONDS apart).

The larger sizes are copies of the real films with new ids, so the data keeps its real
shape (collections, cast sizes, gaps). Each size is run several times and the best
time is kept, because the first run is often slowed by things outside the code.
"""
import time

import numpy as np
import pandas as pd

from pipeline import config
from pipeline.analysis import run_analysis
from pipeline.transform import prepare


def copies(films, cast, directors, n: int):
    """n films made by repeating the real ones, in order. There is no randomness: the same
    films always give the same copies, so the timing data is identical every run.

    Each copy gets new film ids and new collection ids, so copies form their own series
    instead of growing the real ones. Collection ids are renumbered 0, 1, 2 ... per copy,
    so they can never collide however large TMDb's own ids are."""
    reps = int(np.ceil(n / len(films)))
    big = pd.concat([films.assign(copy=k) for k in range(reps)], ignore_index=True).iloc[:n]
    big["old_id"] = big["movie_id"]
    big["movie_id"] = pd.array(np.arange(n) + 100_000_000, dtype="Int64")

    codes, uniques = pd.factorize(big["collection_id"])        # -1 = no collection (standalone)
    new_collection = pd.Series(big["copy"] * len(uniques) + codes, index=big.index, dtype="Int64")
    big["collection_id"] = new_collection.where(codes >= 0)      # standalones stay without a series
    id_map = big[["old_id", "movie_id"]]

    def remap(people):
        return (id_map.merge(people.rename(columns={"movie_id": "old_id"}), on="old_id")
                      .drop(columns="old_id"))

    return big.drop(columns=["copy", "old_id"]), remap(cast), remap(directors)


def time_stages(films, cast, directors) -> dict:
    """Seconds for the two stages Adjoa waits for: cleaning, then the analysis."""
    start = time.perf_counter()
    fact, _ = prepare(films, config.RULES)
    clean = time.perf_counter() - start

    start = time.perf_counter()
    run_analysis(fact, cast, directors)
    return {"clean": clean, "analyse": time.perf_counter() - start}


def time_pipeline(films, cast, directors) -> pd.DataFrame:
    rows = []
    for n in config.TIMING_SIZES:
        f, c, d = copies(films, cast, directors, n)          # made outside the timed part
        runs = pd.DataFrame([time_stages(f, c, d) for _ in range(config.TIMING_REPEATS)])
        best = runs.min()                                   # best of N, per stage
        rows.append({
            "titles": n,
            **{f"{stage}_s": round(s, 4) for stage, s in best.items()},
            "total_s": round(best.sum(), 4),
            "slowest_stage": best.idxmax(),
            "fetch_at_least_s": round(2 * n * config.THROTTLE_SECONDS, 1),
            "within_budget": None if config.TIME_BUDGET_SECONDS is None
                             else bool(best.sum() <= config.TIME_BUDGET_SECONDS),
        })
    table = pd.DataFrame(rows)
    table["growth_vs_previous"] = (table["total_s"] / table["total_s"].shift()).round(2)
    return table
