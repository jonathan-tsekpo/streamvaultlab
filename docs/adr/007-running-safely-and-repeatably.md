# ADR-007: The run must be fast enough for a meeting, stop if the results don't add up, and not store downloaded data in git

**Status:** Accepted · **Date:** 2026-11-20 · **Deciders:** Jonathan (data engineer)

## Context
Adjoa will rerun this every quarter, on her own laptop, sometimes live in a meeting, and without us.
Next year's list will be about 500 titles. Three things must hold:
1. **It must be fast enough to run in a meeting.** The brief gives no time limit, so we set one.
2. **A broken run must never look like a good one.** A partial answer presented as complete is
   worse than no answer. This year 9 of 127 lines (7%) couldn't be used: 1 blank, 3 not ids and
   5 ids TMDb doesn't have. (Repeated lines don't count, because no film is lost.)
3. **Results must be traceable.** We download each film's data from TMDb once and keep it in a local
   folder (the "cache"), so reruns don't download everything again. The question is whether that
   folder goes into the shared code repository (git).

## Decision
1. **Time budget: a rerun must finish within 60 seconds** (`TIME_BUDGET_SECONDS = 60`), long enough
   for a pause in a meeting. We measured it, with downloading excluded (see below):
   | Titles | Analysis time (best of 5 runs) |
   | --- | --- |
   | 127 | 0.17 s |
   | 500 | 0.16 s |
   | 5,000 | 0.16 s |

   A full rerun from the saved data, including loading, checks and writing every table, took about
   11 seconds for this year's list. The analysis has no loops over individual films, so its time
   barely grows with the list. **Downloading is the slow part:** at least 4 minutes for 500 new titles
   and 42 minutes for 5,000, because requests are spaced out to respect TMDb's limits. So Adjoa should
   download before the meeting (`python run_pipeline.py`) and rerun in the meeting from the saved data
   (`python run_pipeline.py --offline`).
2. **Safety checks before anything is saved** (`checks.py`). The run checks that every line and
   every film is accounted for, that no film is counted twice, that both groups exist in both time
   windows, and that **no more than 25% of the list is unusable** (`MAX_UNUSABLE_SHARE = 0.25`).
   If any check fails, the run stops, saves nothing and says why.
3. **The cache is not stored in git** (it's listed in `.gitignore`). Instead, every run records
   the date of the data, the rules used and a fingerprint of every result table in
   `out/run_log.jsonl`. A fresh copy of the project downloads the data again in about a minute.

## Alternatives considered
- **No time budget.** Rejected: "fast enough" can't be checked without a number.
- **No limit on unusable lines.** Rejected: a broken API key or a damaged list could quietly
  produce an answer based on a few films.
- **A strict 5% limit.** Rejected: this year's 7% would stop the run over simple typing errors in the list.
- **Store the cache in git.** Anyone could reproduce the exact numbers offline. Rejected because
  it would copy TMDb's data into our repository (TMDb's terms should be checked first), and because
  Adjoa should work with up-to-date data each year.

## Consequences
A bad run fails loudly with a clear reason, and a good run shows its passed checks in the summary.
A rerun months later may show slightly different numbers if TMDb's data changes. The spot-check
(which compares 10 films with TMDb live) and the fingerprints will show exactly what changed.

## What survives a rerun at 500 titles
Everything. At 500 titles, the run stops if more than 125 lines are unusable, and the timing table
(`timing.csv`) shows each quarter whether the analysis is still within budget.

## Revisit when
Lists become consistently cleaner (then tighten the limit), or someone needs to reproduce the exact
numbers without internet access (then store a dated copy of the data).
