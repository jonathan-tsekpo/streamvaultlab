"""LOAD: write the published tables safely, so a rerun is always safe.

Each table is written to a temporary file first, then swapped into place with
os.replace. Anyone opening the file sees either the old complete version or the new
complete version, never half of one. A short hash of each table goes into the run log,
so you can show that a rerun produced identical results.

CSV, not Parquet: the tables are small, and Kwame's team opens them in Excel.
"""
import hashlib
import os

import pandas as pd

from pipeline import config


def content_hash(df: pd.DataFrame) -> str:
    """Same content -> same 12 characters. Different content -> different."""
    return hashlib.sha256(df.to_csv(index=False).encode("utf-8")).hexdigest()[:12]


def write_table(df: pd.DataFrame, name: str) -> dict:
    target = config.TABLES / f"{name}.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(".tmp")
    df.to_csv(temp, index=False)
    try:
        os.replace(temp, target)             # the swap is all-or-nothing
    except PermissionError:                  # Windows: the file is open in another program
        temp.unlink(missing_ok=True)
        raise PermissionError(f"{target.name} is open in another program (Excel?): close it and rerun") from None
    return {"table": name, "rows": len(df), "hash": content_hash(df)}


def write_all(tables: dict) -> list:
    return [write_table(df, name) for name, df in tables.items()]
