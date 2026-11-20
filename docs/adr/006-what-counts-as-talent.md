# ADR-006: Talent means the director and the top 3 billed actors, each with at least 2 films

**Status:** Accepted · **Date:** 2026-11-20 · **Deciders:** Jonathan (data engineer)

## Context
The brief asks which directors and lead actors signal a title worth licensing. The full cast lists
contain 7,827 entries for 112 films, and most names appear only once. A person with one successful
film proves nothing; it could be luck, or the film's series. Question Q9.

## Decision
- **Lead actors** are the top 3 names in the billing order, the names on the poster
  (`LEAD_CAST_MAX_ORDER = 2`, because billing is counted from 0).
- A name is only shown if it has **at least 2 films** with usable figures (`TALENT_MIN_FILMS = 2`).
- A **hit** is a film that earned at least twice its budget (`HIT_ROI = 2.0`).

Each name is shown with the number of films it's based on, so the reader can judge.

## Alternatives considered
- **Only the top-billed actor.** Rejected: it misses co-stars (e.g. Carrie Fisher alongside Mark Hamill).
- **The top 5 actors.** Rejected: it adds supporting actors who don't sell a film.
- **At least 3 films.** Rejected: too few names would be left on a list of 112 films.

## Consequences
The list of names is short enough to be useful. Two weak points, both stated in the memo:
- **Talent and franchise are tangled together.** Most top names come from one series (Mark Hamill
  and Carrie Fisher: 3 films, all Star Wars), so they tell us about the series, not the person.
  Names with hits across *different* series (Harrison Ford, Steven Spielberg) are more meaningful.
- **The hit rate barely separates anyone**, because almost every film on this list earned twice its budget.

## What survives a rerun at 500 titles
The rules run on their own. With a longer list, more names will reach 2 films, and the talent read
will become more reliable.

## Revisit when
The list is long enough that a 3-film minimum still leaves 10 or more names.
