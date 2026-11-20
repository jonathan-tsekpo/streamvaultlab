# Improvement beyond the brief: a one-page summary that warns when the answer is shaky

## What it is
Every run writes `out/summary.md`: one page with all the results. It shows where every line went,
the checks, the comparison in both windows, the risks, the shortlist candidates, talent, timing and
the spot-check. The run also prints a warning when the answer changes between windows or depends on
a cleaning rule.

## Who it helps
**Adjoa**, who will rerun this next year with about 500 titles, on her own. Without it she would
have to open 20 tables and work out for herself whether the answer still holds.

## What it's worth
- **Time:** checking a run takes minutes, on one page.
- **Fewer mistakes:** this year one result flips with the franchise definition. The warning makes
  sure a flip like that is never missed.
- **Easy to share:** the summary has only public TMDb figures, never the API key.

## How to use it
Run `python run_pipeline.py`, then open `out/summary.md`. Warnings appear in the terminal and in the run log.
