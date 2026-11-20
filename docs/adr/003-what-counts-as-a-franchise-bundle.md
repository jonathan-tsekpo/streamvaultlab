# ADR-003: Any film that belongs to a series counts as franchise, because studios sell the whole series as one bundle

**Status:** Accepted · **Date:** 2026-11-20 · **Deciders:** Jonathan (data engineer)

## Context
Kwame's question is whether to prioritise **franchise bundles** or **standalone hits**, so every film
has to be put in one of the two groups.

The brief says how studios sell: *"a franchise arrives as a bundle (take all six Space Raider films
or none), while standalone hits are priced one at a time."* So a film that belongs to a series can't
be licensed on its own. Kwame would have to take the whole series.

TMDb marks each film that belongs to a series (a "collection"). On Kwame's list, **9 films are the
only film of their series on the list**: Jaws, The Lion King, The Silence of the Lambs, Ghostbusters,
Blade Runner, The Incredibles, Monsters, Inc., The Smurfs and Mad Max: Fury Road (F12). Their sequels
exist, but they aren't on the list. Question Q4.

## Decision
`RULES["franchise_min_on_list"] = 1`. **Any film that belongs to a series counts as franchise**,
including the 9 lone films, because a studio would only sell them as part of their series.

For the **shortlist**, a franchise needs **at least 2 films on the list**. We can't judge a whole
bundle from one film, so the 9 lone films are named in the memo as bundles we couldn't assess.

## Alternatives considered
**Only series with 2+ films on the list count as franchise (setting 2).** This treats the 9 lone
films as standalones. We first chose this, reasoning that Kwame would buy what's on his list. We
rejected it because the brief says studios don't sell a series film on its own: Jaws can't be bought
as a standalone.

This is the **only decision that changes a result** this year:

| Result | Setting 1 (chosen) | Setting 2 |
| --- | --- | --- |
| Typical film since 2000 | franchise ahead, 5.05x vs 3.85x | franchise ahead, 5.05x vs 4.49x |
| Typical film, all years | franchise ahead, 5.62x vs 3.85x | franchise ahead, 5.53x vs 5.00x |
| All money added up since 2000 | franchise ahead, 5.08x vs 4.24x | franchise ahead, 5.10x vs 4.40x |
| All money added up, all years | **franchise** ahead, 5.58x vs 4.85x | **standalone** ahead, 5.59x vs 5.52x |
| Films in each group, all years (since 2000) | 96 vs 16 (63 vs 8) | 87 vs 25 (59 vs 12) |

(5x means a film earned five times its budget.) Under setting 1, franchises lead on every measure
in both windows. Under setting 2, one measure flips to standalone over all years, because Jaws (67x)
and The Lion King (17x) would count as standalones.

## Consequences
- **Better:** the groups match how studios actually sell, and the answer is the same on every
  measure and in both windows.
- **Worse:** the standalone group is small: 16 films, only 8 since 2000 (risk #2 in the findings).
- **A limit we can't remove:** a bundle includes films that aren't on Kwame's list (e.g. the Jaws
  sequels). We only see the listed films, so we can't see the "weak middle entries" his team worries
  about. A bundle's real performance could be lower than our figures. The memo tells Kwame to confirm
  with the studio which films each bundle includes.
- **If we're wrong:** if a studio would sell a series film on its own, the 9 lone films are really
  standalone options, and over all years the "money added up" result leans standalone.

## What survives a rerun at 500 titles
The rule runs on its own. A longer list will include more films from each series, so more bundles
can be judged properly. The column `collection_films_on_list` in `fact_films.csv` shows how many
films of each series are on the list.

## Revisit when
A studio offers single films from a series, or Kwame can get the full film list of each bundle
(then each bundle can be judged as a whole).
