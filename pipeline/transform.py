"""TRANSFORM: turn cached JSON into flat tables, then add the fields the analysis needs.

The grain of each table (what one row means):
  films        one row per film
  cast         one row per film per cast member
  directors    one row per film per director
  fact_films   one row per film in the comparison
  id_account   one row per line of the candidate list

Money rules never remove a film. A budget or revenue judged unknown becomes NaN:
the film still counts as a title, but is left out of the return figures
("flag and exclude per metric").
"""
import numpy as np
import pandas as pd

from pipeline.extract import read_cached
from pipeline.validate import validate_films


# ------------------------------------------------------------- flatten
def film_row(movie: dict) -> dict:
    """One flat dict per film, written by hand.

    Why not json_normalize here? belongs_to_collection is a dict for franchise films
    and null for standalones, so json_normalize would give the two groups different
    columns. Writing the row by hand gives every film the same columns.
    """
    collection = movie.get("belongs_to_collection") or {}    # null = standalone: a fact, not a gap
    genres = movie.get("genres") or []
    return {
        "movie_id": movie.get("id"),
        "title": movie.get("title"),
        "release_date": movie.get("release_date") or None,    # TMDb sends "" when unknown
        "status": movie.get("status"),
        "budget": movie.get("budget"),
        "revenue": movie.get("revenue"),
        "runtime": movie.get("runtime"),
        "collection_id": collection.get("id"),
        "collection_name": collection.get("name"),
        "genres": "|".join(g["name"] for g in genres),        # a list becomes one value per film
        "vote_count": movie.get("vote_count"),
        "vote_average": movie.get("vote_average"),
        "original_language": movie.get("original_language"),
    }


def build_films(movie_ids: list) -> pd.DataFrame:
    films = pd.DataFrame([film_row(read_cached("movie", i)) for i in movie_ids])
    release = pd.to_datetime(films["release_date"], format="%Y-%m-%d", errors="coerce")
    films = films.assign(
        movie_id=films["movie_id"].astype("Int64"),
        release_date=release,
        release_year=release.dt.year.astype("Int64"),
        budget=films["budget"].astype("float64"),             # money stays float: NaN needs it
        revenue=films["revenue"].astype("float64"),
        collection_id=films["collection_id"].astype("Int64"),
        vote_count=films["vote_count"].astype("Int64"),
    )
    assert films["movie_id"].is_unique, "films must be one row per film"
    return films


def build_people(movie_ids: list) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Expand each film's cast and crew lists into one row per person.

    record_path picks the list to expand; meta keeps the film's id on every row;
    meta_prefix stops the film's "id" clashing with each person's "id".
    """
    credits = [read_cached("credits", i) for i in movie_ids]
    options = dict(meta=["id"], meta_prefix="movie_")

    cast = pd.json_normalize(credits, record_path="cast", **options)
    cast = cast.rename(columns={"id": "person_id"}).reindex(
        columns=["movie_id", "person_id", "name", "character", "order"])      # same columns even if empty

    crew = pd.json_normalize(credits, record_path="crew", **options).rename(columns={"id": "person_id"})
    crew = crew.reindex(columns=["movie_id", "person_id", "name", "job"])
    directors = crew.loc[crew["job"].eq("Director"), ["movie_id", "person_id", "name"]].drop_duplicates()

    cast["movie_id"] = cast["movie_id"].astype("Int64")
    directors["movie_id"] = directors["movie_id"].astype("Int64")
    return cast.reset_index(drop=True), directors.reset_index(drop=True)


def build_tables(acquisition: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Flatten every film whose details came back 200."""
    found = acquisition["movie_status"].eq("200")
    with_credits = found & acquisition["credits_status"].eq("200")
    films = build_films(acquisition.loc[found, "movie_id"].tolist())
    cast, directors = build_people(acquisition.loc[with_credits, "movie_id"].tolist())
    assert len(films) == found.sum(), "a film was lost while flattening"
    return films, cast, directors


# ------------------------------------------------------------- derive
def clean_money(films_in: pd.DataFrame, rules: dict) -> pd.DataFrame:
    """Apply the money rules, then add roi, collection size and group. Never removes a film."""
    budget, revenue = films_in["budget"], films_in["revenue"]
    tiny = rules["tiny_money_threshold"]

    budget_unknown = budget.isna() | (budget.eq(0) & rules["zero_budget_is_unknown"]) \
        | (budget.gt(0) & budget.lt(tiny) & rules["tiny_money_is_unknown"])
    revenue_unknown = revenue.isna() | (revenue.eq(0) & rules["zero_revenue_is_unknown"]) \
        | (revenue.gt(0) & revenue.lt(tiny) & rules["tiny_money_is_unknown"])

    fact = films_in.assign(
        budget_clean=budget.mask(budget_unknown),
        revenue_clean=revenue.mask(revenue_unknown),
        money_changed=(budget_unknown & budget.notna()) | (revenue_unknown & revenue.notna()),
    )
    fact["roi"] = (fact["revenue_clean"] / fact["budget_clean"]).where(fact["budget_clean"] > 0)

    # How many films of the same collection are on the list (NaN for standalones).
    on_list = fact.groupby("collection_id")["movie_id"].transform("count")
    is_franchise = fact["collection_id"].notna() & on_list.ge(rules["franchise_min_on_list"]).fillna(False)
    fact["collection_films_on_list"] = on_list.astype("Int64")
    fact["group"] = np.where(is_franchise, "franchise", "standalone")   # never null, so groupby keeps every film

    assert len(fact) == len(films_in), "clean_money must not add or remove films"
    return fact


def prepare(films: pd.DataFrame, rules: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """All the cleaning under one set of rules: returns (fact_films, film_quarantine)."""
    films_in, quarantine = validate_films(films, rules)
    return clean_money(films_in, rules), quarantine


# ------------------------------------------------------------- the id account
def id_account(lines, id_quarantine, acquisition, film_quarantine) -> pd.DataFrame:
    """One row per line of the candidate list, saying where it ended up.

    validate= on each merge proves the join can't add or lose a line.
    """
    ids = lines[["source_line", "raw_value"]].merge(
        id_quarantine[["source_line", "reason", "duplicate_of_line"]],
        on="source_line", how="left", validate="one_to_one")
    ids["movie_id"] = pd.to_numeric(ids["raw_value"].str.strip(), errors="coerce").astype("Int64")
    ids = ids.merge(acquisition[["movie_id", "movie_status"]], on="movie_id", how="left",
                    validate="many_to_one")
    ids = ids.merge(film_quarantine[["movie_id", "reason"]].rename(columns={"reason": "film_reason"}),
                    on="movie_id", how="left", validate="many_to_one")
    assert len(ids) == len(lines), "the id account gained or lost a line"

    usable = ids["reason"].isna()
    ids["outcome"] = np.select(
        [~usable,
         ids["movie_status"].eq("404").fillna(False),
         ids["movie_status"].str.startswith("error").fillna(False),
         ids["movie_status"].eq("not cached").fillna(False),
         ids["film_reason"].notna()],
        [ids["reason"],
         "not found on TMDb (404)",
         "fetch failed",
         "not fetched (offline)",
         "excluded: " + ids["film_reason"].fillna("")],
        default="in analysis",
    )
    return ids.drop(columns="film_reason")
