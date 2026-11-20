"""VALIDATE: split rows into kept and quarantined, each rejected row with ONE reason.

Nothing is dropped silently: kept + quarantined always equals what came in, so the
id account can say where every line of the candidate list went.

  validate_ids    lines of id_list.csv -> usable unique ids  + quarantined lines
  validate_films  fetched films        -> films for analysis + quarantined films

np.select checks the conditions in order and gives each row the FIRST reason that
applies, or "" if none does. That is how every row gets exactly one reason.
"""
import numpy as np
import pandas as pd

from pipeline import config

MAX_ID_DIGITS = 9      # TMDb ids are well under a billion; longer numbers are not ids


def validate_ids(lines: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (ids, quarantine).

    ids: one row per usable id, from the first line it appears on.
    quarantine: every other line, with its reason.

    Spaces are stripped and the id converted to a number before looking for
    duplicates, so " 603", "0603" and "603" count as the same film.
    """
    text = lines["raw_value"].str.strip()
    is_id = text.str.fullmatch(r"\d+") & text.str.len().le(MAX_ID_DIGITS)   # too long = not an id, never a crash
    movie_id = pd.to_numeric(text.where(is_id), errors="coerce").astype("Int64")
    is_repeat = movie_id.notna() & movie_id.duplicated()          # keeps the first appearance

    reason = np.select(
        [text.eq(""), movie_id.isna(), is_repeat],
        ["blank line", "not a TMDb id", "duplicate line"],
        default="",
    )
    lines = lines.assign(movie_id=movie_id, reason=reason)
    first_line = lines.groupby("movie_id")["source_line"].transform("min")
    lines["duplicate_of_line"] = first_line.where(lines["reason"].eq("duplicate line")).astype("Int64")

    kept = lines["reason"].eq("")
    ids = lines.loc[kept, ["source_line", "raw_value", "movie_id"]].reset_index(drop=True)
    quarantine = lines.loc[~kept].reset_index(drop=True)

    assert len(ids) + len(quarantine) == len(lines), "a line was lost or counted twice"
    assert ids["movie_id"].is_unique, "kept ids must be unique"
    return ids, quarantine


def money_unknown(amount: pd.Series, zero_is_unknown: bool, rules: dict) -> pd.Series:
    """True where a budget or revenue can't be trusted (ADR-001): missing, 0 (if that rule is on),
    or above 0 but under the tiny-money threshold (if that rule is on).
    One definition, used by the duplicate tiebreak below and by transform.clean_money()."""
    tiny = (amount.gt(0) & amount.lt(rules["tiny_money_threshold"])) & rules["tiny_money_is_unknown"]
    return amount.isna() | (amount.eq(0) & zero_is_unknown) | tiny


def title_year_key(films: pd.DataFrame) -> pd.Series:
    """Title + year with case and spacing ignored, to spot one film listed under two ids."""
    return (films["title"].fillna("").str.strip().str.lower() + " | "
            + films["release_year"].astype("string").fillna("?"))


def validate_films(films: pd.DataFrame, rules: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (films_in, quarantine). These rules remove a film from the comparison.

    The money rules never remove a film: they live in transform.clean_money().
    """
    not_released = films["status"].ne("Released") & rules["released_only"]
    has_runtime = films["runtime"].gt(0)                      # 0 or missing = runtime unknown, not short
    short = (has_runtime & films["runtime"].lt(rules["short_film_minutes"])).fillna(False) \
        & rules["exclude_short_films"]

    # For a title listed twice, keep a copy that passed the rules above, then one with
    # usable money, then the lowest id.
    has_money = (~money_unknown(films["budget"], rules["zero_budget_is_unknown"], rules)
                 & ~money_unknown(films["revenue"], rules["zero_revenue_is_unknown"], rules)
                 & films["budget"].gt(0))                    # the same money rule as the analysis
    order = films.assign(_key=title_year_key(films), _out=not_released | short, _money=has_money)
    order = order.sort_values(["_key", "_out", "_money", "movie_id"],
                              ascending=[True, True, False, True])
    later_copies = order.index[order["_key"].duplicated()]     # row labels of every copy after the first
    second_copy = films.index.isin(later_copies) & rules["drop_same_title_and_year"]

    reason = np.select(
        [not_released, short, second_copy],
        ["not released", f"short film (under {rules['short_film_minutes']} min)",
         "same film listed under another id"],
        default="",
    )
    kept = reason == ""
    films_in = films[kept].reset_index(drop=True)
    quarantine = films.loc[~kept, ["movie_id", "title", "release_year", "status", "runtime"]].assign(
        reason=reason[~kept]).reset_index(drop=True)

    assert len(films_in) + len(quarantine) == len(films), "a film was lost or counted twice"
    return films_in, quarantine
