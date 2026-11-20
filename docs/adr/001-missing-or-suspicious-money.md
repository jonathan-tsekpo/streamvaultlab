# ADR-001: Missing or suspicious money figures are treated as "unknown"

**Status:** Accepted · **Date:** 2026-11-20 · **Deciders:** Jonathan (data engineer)

## Context
Every comparison in this analysis depends on two figures per film: its **budget** (what it cost to
make) and its **revenue** (what it earned at the box office). TMDb, our data source, is filled in
by volunteers, and two kinds of bad figure are common:
- **0**, which usually means nobody entered the number, not that the film cost or earned nothing;
- **very small amounts**, such as a budget of 12, where $12 million was meant (a typing error).

If we used these figures as they are, a film could show a return of 0x (a failure that never
happened) or of millions of times its budget (a success that never happened). This year, **no film
on Kwame's list has either problem** (findings F5 and F6), but next year's longer list probably will.
Questions Q1–Q3.

## Decision
- A budget or revenue of **0** is treated as unknown: `RULES["zero_budget_is_unknown"] = True`,
  `RULES["zero_revenue_is_unknown"] = True`.
- An amount **above $0 but under $1,000** is treated as unknown: `RULES["tiny_money_is_unknown"] = True`,
  `RULES["tiny_money_threshold"] = 1_000`.

A film with an unknown figure **stays on the list and in the title counts**, but is left out of
the return calculations. The summary shows both numbers ("titles" and "usable"), so the reader can
see how much is missing.

## Alternatives considered
- **Use the figures as they are.** Rejected: one wrong figure could distort a whole group's result.
- **Remove the film completely.** Rejected: it would vanish from the counts and hide how much of
  the list we couldn't measure.
- **Correct the figure (e.g. turn 12 into 12,000,000).** Rejected: that is a guess presented as data.

The sensitivity check (which reruns the analysis with each rule switched on and off) shows these
rules change nothing this year.

## Consequences
Return figures use only believable numbers, and missing data is visible rather than hidden. The
downside: a genuinely unprofitable film with a recorded 0 would be hidden. This year that costs nothing.

## What survives a rerun at 500 titles
The rules run on their own. Adjoa should compare the "titles" and "usable" columns in the summary.
A big gap means a lot of money data is missing.

## Revisit when
More than 1 in 10 films in either group has an unknown figure, or the missing figures are mostly
in one group (that would make the comparison unfair).
