"""Every path, setting and judgement call the pipeline depends on, in one place.

Two kinds of setting:
  SETTINGS   paths, the API, politeness, the QA gate. Plumbing.
  DECISIONS  judgement calls the brief leaves open. Each has a starting value so the
             code runs, but the value is not a recommendation: every DECISION needs
             an ADR in docs/adr/, and out/tables/sensitivity.csv shows the answer
             under the alternatives.

Other modules read these as config.NAME, so changing a value here changes the whole run.
"""
from pathlib import Path

# ============================================================== SETTINGS
ROOT = Path(__file__).resolve().parent.parent
ID_FILE = ROOT / "data" / "id_list.csv"      # the candidate list from Evalu8
CACHE = ROOT / "cache"                       # raw TMDb responses, saved before parsing
OUT = ROOT / "out"
TABLES = OUT / "tables"                      # published tables (CSV)
RUN_LOG = OUT / "run_log.jsonl"              # one JSON line per run
SUMMARY = OUT / "summary.md"                 # the results in one file, for review

# TMDb API. The key is read from .env (TMDB_API_KEY)
API_BASE = "https://api.themoviedb.org/3"
TIMEOUT = (3.05, 20)                         # seconds: (connect, read)
THROTTLE_SECONDS = 0.25                      # pause between live calls: it's a shared free API
RETRY_TOTAL = 5                              # retries for 429 and 5xx only, with backoff
USER_AGENT = "streamvault-lab/1.0 (AmaliTech DE02 coursework)"

WINDOW_START_YEAR = 2000                     # ADR-005: compare all years and 2000 onward; lead with 2000 onward

# QA gate: if any check fails, nothing is written.
MAX_UNUSABLE_SHARE = 0.25                    # ADR-007: stop if more than 25% of list lines can't be analysed

# Timing (fetching excluded). Put the brief's budget here in seconds, or leave None.
TIMING_SIZES = (127, 500, 5000)
TIMING_REPEATS = 5                           # best of 5 runs
TIME_BUDGET_SECONDS = None

# Spot-check: decided BEFORE looking at the results.
SPOT_CHECK_SEED = 42
MONEY_TOLERANCE = 0                          # TMDb stores whole dollars, so compare exactly

# ============================================================== DECISIONS
# The cleaning rules. They are passed around as a dict so the sensitivity analysis
# can rerun the whole comparison with any of them switched.
RULES = {
    "zero_budget_is_unknown": True,      # ADR-001: is a budget of 0 "unknown" or a real zero?
    "zero_revenue_is_unknown": True,     # ADR-001: same question for revenue
    "tiny_money_is_unknown": True,       # ADR-001: is money above 0 but below the threshold an error?
    "tiny_money_threshold": 1_000,       # ADR-001: e.g. 12 probably meant $12 million
    "released_only": True,               # ADR-002: leave unreleased films out of the comparison?
    "exclude_short_films": True,         # ADR-002: shorts are a different population from features
    "short_film_minutes": 40,
    "drop_same_title_and_year": True,    # ADR-002: same title + year under two ids = one film twice?
    "franchise_min_on_list": 2,          # ADR-003: 1 = any film TMDb puts in a collection;
                                         #          2 = only collections with 2+ films on the list
}

HEADLINE_METRIC = "median_roi"           # ADR-004: "median_roi" or "ratio_of_totals" (both are computed)
MIN_GROUP_SIZE = 3                       # ADR-004: smallest group we draw a conclusion from

LEAD_CAST_MAX_ORDER = 2                  # ADR-006: billing order 0, 1, 2 = the top three billed
TALENT_MIN_FILMS = 2                     # ADR-006: films with a usable return before a name counts
HIT_ROI = 2.0                            # ADR-006: a "hit" earns at least 2x its budget

STANDALONE_MIN_VOTES = 50                # shortlist: enough TMDb votes to be a known title
