# Improvement beyond the brief: a one-page summary that warns when the answer is shaky

## What it is
Every run writes `out/summary.md`: one page with all the results. It shows where every line went,
the checks, the comparison in both windows, the risks, the shortlist candidates, talent, timing and
the spot-check. The run also prints a warning when the answer changes between windows or depends on
a cleaning rule.

## Who it helps
**Adjoa**, who reruns this every quarter on her own laptop, sometimes live in a meeting, and next year
with about 500 titles. Without it she would have to open 20 tables in front of the room and work out
for herself whether the answer still holds.

## What it's worth
- **Time:** a rerun from saved data takes about 11 seconds, and the answer is on one page, so she
  can rerun and read it during a meeting.
- **Fewer mistakes:** this year one measure would flip if the franchise definition changed. If a future
  list makes the answer change between windows or depend on a rule, the run says so in capital
  letters, so Adjoa can't miss it, which is exactly what the brief asks for ("say so loudly").
- **Easy to share:** the summary has only public TMDb figures, never the API key.

## How to use it
Run `python run_pipeline.py`, then open `out/summary.md`. Warnings appear in the terminal and in the run log.
