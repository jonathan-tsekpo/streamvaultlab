# ADR-004: The memo leads with the typical film's return; "all money added up" is shown beside it

**Status:** Accepted · **Date:** 2026-11-20 · **Deciders:** Jonathan (data engineer)

## Context
A film's **return** is its box office divided by its budget: 5x means it earned five times what it
cost to make. There are two common ways to compare the return of two groups:

- **The typical film (the median):** line the films up from lowest to highest return and take the
  one in the middle. Every film counts equally, so one huge hit can't move it much.
- **All money added up:** total box office of the group ÷ total budget of the group. This treats
  the group as one investment. Big films count more.

This year both measures favour franchises, in both windows. But "all money added up" is fragile.
It flips to standalone over all years if lone series films are counted as standalones (ADR-003),
and a few extreme hits weigh heavily on it: four films earned between 32 and 70 times their budget
(F11). Question Q8.

## Decision
`HEADLINE_METRIC = "median_roi"`. The memo leads with the **typical film** and shows "all money added
up" next to it.
`MIN_GROUP_SIZE = 3`: a group with fewer than 3 usable films is marked as too small to draw a conclusion.

## Alternatives considered
- **Lead with "all money added up".** It's a fair way to see a group as one investment, but here it
  changes with the franchise definition, and one film can swing it. Also, Kwame doesn't pay the
  production budget; he pays a licensing fee, so "money in, money out" doesn't describe his deal directly.
- **The average (mean).** Rejected: a few huge hits pull it up. The standalone average is 8.3x
  while the typical standalone film earned 3.8x.

**Evidence:** the typical film puts franchises ahead in **all 16** combinations of cleaning rules we
tested, in both windows. "All money added up" over all years splits 8 to 8.

## Consequences
- **Better:** the headline can't be swung by one film or one rule choice, and it matches how Kwame
  works: one deal at a time.
- **Worse:** it ignores size. A typical franchise film also earns far more in total ($787M vs $283M at
  the box office since 2000). The memo includes this.
- **If we're wrong:** if Kwame thinks of all deals as one pot of money, the answer is the same this
  year (franchise), but less secure.

## What survives a rerun at 500 titles
Both measures are always calculated, and the run prints a warning when they point different ways.

## Revisit when
The list has 50 or more standalone films, or Kwame says he judges deals as one combined investment.
