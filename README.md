# StreamVault licensing analysis

A production-style pipeline in plain Python, pandas and requests. It takes Kwame's candidate list
(one column of TMDb ids), fetches every film's details and credits from the TMDb API politely and
with a cache, accounts for every line of the list, and compares franchise bundles with standalone
films for **all years** and **2000 onward**. It also produces a shortlist, a talent read, a timing
report and a spot-check against the live API.

```text
 data/id_list.csv ──────┐
 TMDb API (cached) ─────┤
                        ▼
 EXTRACT ──► VALIDATE ──► TRANSFORM ──► ANALYSE ──► QA GATE ──► LOAD ──► out/tables/*.csv
 extract.py  validate.py  transform.py  analysis.py  checks.py  load.py   out/summary.md
                                        diagnose.py              then timing.py, spot_check.py
 └────────── run in order, timed, logged to out/run_log.jsonl by run_pipeline.py ──────────┘
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

1. Put the candidate list from Evalu8 at `data/id_list.csv`.
2. Open `.env` and replace `paste-your-key-here` with your TMDb API key: `TMDB_API_KEY=abc123...`
   (no quotes, no spaces). `.env` is in `.gitignore`, so the key is never committed. If `.env` is
   missing, copy `.env.example` to `.env`.

## Run

```bash
python run_pipeline.py              # first run fetches (2 calls per film); later runs use the cache
python run_pipeline.py --offline    # never touch the network
python run_pipeline.py --refresh    # take a new TMDb snapshot
python run_pipeline.py --quick      # skip the timing and the live spot-check
```

Every run writes `out/summary.md`: all the results in one readable file. Rerun as often as you
like. Tables are replaced safely, and the hashes in `out/run_log.jsonl` show whether a rerun gave
identical content (`timing` and `spot_check` change every run by design). Next year: replace
`data/id_list.csv` and run the same command.

Open `explore/profile_candidates.ipynb` in VS Code to look at the rows behind the numbers.
Clear its outputs before committing.

## Layout

| Path | What it holds | Why it's separate |
| --- | --- | --- |
| `pipeline/` | Production code: one file per stage | This is what runs. Nothing else lives here |
| `pipeline/config.py` | Every path, setting and **DECISION** | One place to see every assumption |
| `run_pipeline.py` | The orchestrator | The one command Adjoa runs |
| `data/id_list.csv` | The candidate list from Evalu8 | The input. Committed: the pipeline can't run without it |
| `docs/findings.md` | The data diagnosis, ranked by risk, each finding traced to code | The evidence behind every rule |
| `docs/questions.md` | Questions we couldn't ask Kwame, and what we decided | Business meaning, decided openly |
| `docs/adr/` | Decision notes, one per judgement call | The why behind the code, versioned with it |
| `docs/data_contract.md` | What we expect from the list and the API, and what happens if it's broken | Both sides know the rules |
| `docs/memo.md`, `docs/improvement.md` | The memo to Kwame and the improvement beyond the brief | What reaches the client |
| `explore/` | The investigation notebook | Exploring is kept apart from production code |
| `cache/`, `out/` | Raw API responses and outputs | Rebuilt by the code (committing `cache/` is ADR-007) |

## Outputs (`out/tables/`)

| Table | One row per | What it answers |
| --- | --- | --- |
| `id_account` | line of the list | Where every title went |
| `id_quarantine`, `film_quarantine` | rejected line / excluded film | Why it was left out |
| `acquisition` | id | What TMDb returned, and when |
| `films`, `cast`, `directors` | film; film per person | The flattened data |
| `fact_films` | film in the comparison | Cleaned money, return, group |
| `films_flagged`, `findings`, `missing_vs_present` | film; flag | Raw material for the diagnosis |
| `kpis` | window per group | Franchise vs standalone, measured two ways, with group sizes |
| `sensitivity`, `flips` | rule combination | Does any decision change the answer? |
| `franchise_candidates`, `standalone_candidates` | collection; film | Raw material for the shortlist |
| `talent_directors`, `talent_leads` | person | Who signals a title worth licensing |
| `timing` | size | Seconds per stage at 127 / 500 / 5,000 titles |
| `spot_check` | sampled film per field | Our output vs live TMDb, each difference classified |

