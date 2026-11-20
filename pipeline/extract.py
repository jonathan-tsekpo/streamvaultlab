
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from pipeline import config

ENDPOINTS = {"movie": "/movie/{id}", "credits": "/movie/{id}/credits"}


class ApiKeyError(Exception):
    """The TMDb key is missing or rejected. Nothing will work until it's fixed."""


# ------------------------------------------------------------- the candidate list
def read_id_list(path: Path = None) -> pd.DataFrame:
    """One row per line of the file: source_line and raw_value (text, untouched).

    keep_default_na=False keeps "N/A" and blanks as text instead of turning them into NaN.
    skip_blank_lines=False stops pandas silently dropping empty lines.
    Together they mean every line of the file can be accounted for.
    """
    path = path or config.ID_FILE
    if not path.exists():
        raise FileNotFoundError(f"put id_list.csv from Evalu8 at {path}")

    raw = pd.read_csv(path, dtype="string", keep_default_na=False, skip_blank_lines=False)
    first_line = 2                                     # line 1 was the header
    if raw.columns[0].strip().isdigit():               # no header: the "header" was an id
        raw = pd.read_csv(path, header=None, dtype="string", keep_default_na=False,
                          skip_blank_lines=False)
        first_line = 1

    lines = pd.DataFrame({"raw_value": raw.iloc[:, 0]})
    lines.insert(0, "source_line", range(first_line, first_line + len(lines)))
    return lines


# ------------------------------------------------------------- TMDb
def make_session() -> requests.Session:
    """One Session for every call, with the key and the retry rules set once."""
    key = os.environ.get("TMDB_API_KEY", "").strip()
    if not key or key == "paste-your-key-here":
        raise ApiKeyError("put your TMDb key in .env as TMDB_API_KEY=yourkey")

    retry = Retry(
        total=config.RETRY_TOTAL,
        backoff_factor=1,                              # waits grow: 1, 2, 4, 8 ... seconds
        status_forcelist=(429, 500, 502, 503, 504),    # temporary failures only
        allowed_methods=["GET"],
        respect_retry_after_header=True,
        raise_on_status=False,                         # we look at the final status ourselves
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers["User-Agent"] = config.USER_AGENT
    session.params = {"api_key": key}
    return session


def get(session: requests.Session, endpoint: str, movie_id: int) -> requests.Response:
    """One live GET. A 401 stops everything; every other status is the caller's to judge."""
    url = config.API_BASE + ENDPOINTS[endpoint].format(id=movie_id)
    response = session.get(url, timeout=config.TIMEOUT)
    if response.status_code == 401:
        raise ApiKeyError("TMDb rejected the key (401): check TMDB_API_KEY in .env")
    return response


def cache_file(endpoint: str, movie_id: int) -> Path:
    return config.CACHE / endpoint / f"{movie_id}.json"


def read_cached(endpoint: str, movie_id: int) -> dict:
    return json.loads(cache_file(endpoint, movie_id).read_text(encoding="utf-8"))


def fetch_all(movie_ids: list, refresh: bool = False, offline: bool = False) -> pd.DataFrame:
    """Make sure every id has a details and a credits result, from the cache or live.

    Returns one row per id: movie_id, movie_status, movie_fetched_at, credits_status,
    credits_fetched_at. Statuses are text: "200", "404", "not cached" (offline run), or
    "error 503" (still failing after the retries). attrs["requests_made"] counts live calls.

    The manifest (cache/manifest.json) remembers each call's status and time, so
    404s are never asked twice and the snapshot date is known.
    """
    manifest_file = config.CACHE / "manifest.json"
    manifest = json.loads(manifest_file.read_text()) if manifest_file.exists() else {}
    session = None
    requests_made = 0
    rows = []
    try:
        for movie_id in movie_ids:
            row = {"movie_id": movie_id}
            for endpoint in ENDPOINTS:
                key = f"{endpoint}:{movie_id}"
                remembered = manifest.get(key, {}).get("status")

                if not refresh and cache_file(endpoint, movie_id).exists():
                    status = "200"
                elif not refresh and remembered == "404":
                    status = "404"
                elif offline:
                    status = "not cached"
                else:
                    session = session or make_session()
                    response = get(session, endpoint, movie_id)
                    requests_made += 1
                    status = str(response.status_code)
                    if status == "200":
                        path = cache_file(endpoint, movie_id)
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text(response.text, encoding="utf-8")   # raw, before parsing
                    elif status != "404":
                        status = f"error {status}"
                    manifest[key] = {"status": status,
                                     "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
                    time.sleep(config.THROTTLE_SECONDS)

                row[f"{endpoint}_status"] = status
                row[f"{endpoint}_fetched_at"] = manifest.get(key, {}).get("fetched_at")
            rows.append(row)
    finally:                                   # saved even if the run crashes halfway
        manifest_file.parent.mkdir(parents=True, exist_ok=True)
        manifest_file.write_text(json.dumps(manifest, indent=1, sort_keys=True))
        if session is not None:
            session.close()

    acquisition = pd.DataFrame(rows)
    assert len(acquisition) == len(movie_ids), "an id was lost or fetched twice"
    acquisition.attrs["requests_made"] = requests_made
    return acquisition
