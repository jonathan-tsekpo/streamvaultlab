# Data contract: the candidate list and the TMDb responses

What the pipeline expects to receive, written from what we **observed**, what it does when an
expectation is broken, and where. Fill "Seen in the data" from your run (`out/summary.md`).

**Parties:** Kwame's team (sends the candidate list), TMDb (public API, no agreement), the data
team (receives) · **Version:** 1.0

## The candidate list: `data/id_list.csv`

| Rule | If it's broken | Where |
| --- | --- | --- |
| One CSV file, one column of TMDb movie ids; a header row is optional | Missing file: the run stops with "put id_list.csv from Evalu8 at ..." | `pipeline/extract.py` |
| Every line is read as text, blanks kept, nothing converted | — | `pipeline/extract.py` |

| Value | Rule | Seen in the data | If a line breaks it | Where |
| --- | --- | --- | --- | --- |
| id | Digits only (spaces around it are removed first) | 3 lines: `-1` (line 30), `tt0468569` (line 95, an IMDb id), `N/A` (line 111) | Quarantined: "not a TMDb id" | `pipeline/validate.py` |
| id | Not blank | 1 blank line (line 69) | Quarantined: "blank line" | `pipeline/validate.py` |
| id | Each film listed once (compared as a number, so `0603` = `603`) | 6 repeats (lines 43, 60, 90, 91, 94, 102) | First line kept; the rest quarantined: "duplicate line" | `pipeline/validate.py` |

## TMDb: `GET /movie/{id}` and `GET /movie/{id}/credits`

| Rule | If it's broken | Where |
| --- | --- | --- |
| A valid key in `.env` as `TMDB_API_KEY` | `ApiKeyError`: the run stops at once, no retries | `pipeline/extract.py` |
| The id exists (seen: 5 ids don't exist, see F4) | 404 recorded and remembered, never asked again; line reported "not found on TMDb (404)" | `pipeline/extract.py` |
| Temporary failures (429, 5xx) | Retried up to 5 times with growing waits, obeying Retry-After. Still failing: the QA gate stops the run; the next run asks only for what's missing | `pipeline/extract.py`, `pipeline/checks.py` |

| Field | Rule | Seen in the data | If a film breaks it | Where |
| --- | --- | --- | --- | --- |
| `budget`, `revenue` | Whole dollars; 0 and amounts under $1,000 handled by the money rules | None: every film has both figures above $1,000 | Marked unknown: the film stays, but is left out of return figures | `pipeline/transform.py` |
| `status` | "Released" | All 112 released | Excluded: "not released" | `pipeline/validate.py` |
| `runtime` | Feature length (40+ minutes) | All feature length | Excluded: "short film" | `pipeline/validate.py` |
| `release_date` | `YYYY-MM-DD` or empty | All 112 dated; 41 before 2000 | Kept; a film with no date appears only in "all years" | `pipeline/transform.py`, `pipeline/analysis.py` |
| `belongs_to_collection` | A collection, or null for a standalone film | 96 films in 32 collections; 9 collections have only one film on the list | null = standalone (a fact, not a gap) | `pipeline/transform.py` |
| `cast`, `crew` | Lists, possibly empty | 7,827 cast rows and 122 director rows for 112 films; every film has cast and at least one director | An empty list gives no rows for that film | `pipeline/transform.py` |

## The run as a whole (QA gate)

| Rule | If it's broken | Where |
| --- | --- | --- |
| Every line of the list ends up kept or quarantined with one reason | The run stops; nothing is written | `pipeline/checks.py` |
| Every usable id fetched exactly once, none left unfinished | The run stops | `pipeline/checks.py` |
| Every fetched film flattened, and either in the comparison or excluded with a reason | The run stops | `pipeline/checks.py` |
| One row per film after every join | The run stops (merges also use `validate=`) | `pipeline/checks.py`, `pipeline/transform.py` |
| Both groups present in both windows | The run stops | `pipeline/checks.py` |
| At most 25% of lines unusable (`MAX_UNUSABLE_SHARE`) | The run stops | `pipeline/checks.py` |
