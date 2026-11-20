# ADR-004: The memo leads with the typical film's return; "all money added up" is shown beside it

**Status:** Accepted · **Date:** 2026-11-20 · **Deciders:** Jonathan (data engineer)

## Context
A film's **return** is its box office divided by its budget: 5x means it earned five times what it
cost to make. There are two common ways to compare the return of two groups:

- **The typical film (the median):** line the films up from lowest to highest return and take the
  one in the middle. Every film counts equally, so one huge hit can't move it much.
- **All money added up:** total box office of the group ÷ total budget of the group. This treats
  the group as one investment. Big films count more.

Over all years, the two measures disagree. The typical film says **franchise** (5.53x vs 5.00x).
All money added up says **standalone** (5.59x vs 5.52x). The second result is driven by a few very
old hits: Jaws earned 67 times its budget, and it sits in a standalone group of only 25 films.
Question Q8.

## Decision
`HEADLINE_METRIC = "median_roi"`. The memo leads with the **typical film**, and shows "all money added
up" next to it, with a sentence explaining why they differ.
`MIN_GROUP_SIZE = 3`: a group with fewer than 3 usable films is marked as too small to draw a conclusion.

## Alternatives considered
- **Lead with "all money added up".** It's a fair way to see the group as one investment, but here
  it changes when we change the franchise definition (ADR-003) or the time window (ADR-005), and one
  film can decide it. Also, Kwame doesn't pay the production budget; he pays a licensing fee. So
  "money in, money out" doesn't describe his deal directly.
- **The average (mean).** Rejected: a few huge hits pull it up. The standalone average is 10.5x
  while the typical standalone film earned 5.0x.

**Evidence:** the typical film puts franchises ahead in **all 16** combinations of cleaning rules
we tested, in both time windows. "All money added up" over all years splits 8 to 8.

## Consequences
- **Better:** the headline can't be swung by one film or one rule choice, and it matches how Kwame
  works: one deal at a time.
- **Worse:** it ignores size. A typical franchise film doesn't just earn slightly more per dollar; it
  also earns much more in total ($796M vs $450M at the box office since 2000). The memo includes this.
- **If we're wrong:** if Kwame thinks of the deals as one pot of money, the all-years result is a
  near-tie that leans standalone.

## What survives a rerun at 500 titles
Both measures are always calculated, and the run prints a warning when they point different ways.
With more standalone films, "all money added up" will depend less on single films.

## Revisit when
The list has 50 or more standalone films, or Kwame says he judges deals as one combined investment.
