# ADR-003: A franchise bundle is 2 or more films of the same series on Kwame's list

**Status:** Accepted · **Date:** 2026-11-20 · **Deciders:** Jonathan (data engineer)

## Context
Kwame's question is whether to prioritise **franchise bundles** or **standalone hits**. So every
film has to be put in one of the two groups, and that needs a definition.

TMDb marks a film as part of a series (a "collection") if it has any sequels or prequels at all,
even if those aren't on Kwame's list. On this list, **9 films are the only film of their series**:
Jaws, The Lion King, The Silence of the Lambs, Ghostbusters, Blade Runner, The Incredibles,
Monsters, Inc., The Smurfs and Mad Max: Fury Road (F12).

The usual definition of a franchise is a story or brand that continues across several films. By
that definition, Jaws is a franchise. But Kwame isn't classifying stories; he is deciding what to
**buy**. A bundle means several films bought in one deal. If only one Jaws film is on his list, what he
would actually negotiate is a single-film deal. Question Q4.

## Decision
`RULES["franchise_min_on_list"] = 2`. We group films by **what Kwame would be buying from this list**.
A series counts as a franchise bundle only if 2 or more of its films are on the list. The 9 lone
films are treated as standalone deals.

## Alternatives considered
**Any film in a series is a franchise (setting 1).** This matches the general definition, but it
treats a one-film deal as a bundle, which doesn't match Kwame's decision.

This is the **only decision that changes an answer** this year:

| Result | Setting 1 (any series) | Setting 2 (chosen) |
| --- | --- | --- |
| Typical film since 2000 | franchise ahead, 5.05x vs 3.85x | franchise ahead, 5.05x vs 4.49x |
| Typical film, all years | franchise ahead, 5.62x vs 3.85x | franchise ahead, 5.53x vs 5.00x |
| All money added up, all years | **franchise** ahead, 5.58x vs 4.85x | **standalone** ahead, 5.59x vs 5.52x |
| Films in each group, all years | 96 franchise, 16 standalone | 87 franchise, 25 standalone |

(5x means a film earned five times its budget.)

## Consequences
- **Better:** the groups match the deals Kwame would actually sign, and the standalone group grows
  from 16 to 25 films, which gives more evidence.
- **Worse:** the franchise lead becomes smaller, and the "all money added up, all years" result moves
  to standalone. The memo says this openly.
- **If we're wrong:** if Kwame can also license the missing sequels (e.g. the rest of the Jaws
  films), those 9 titles are really bundle opportunities, and the case for franchises is stronger
  than we report.

## What survives a rerun at 500 titles
The rule runs on its own. A longer list will include more sequels, so fewer films will be alone in
their series and the two settings will give closer answers. The column `collection_films_on_list`
in `fact_films.csv` shows how many films of each series are on the list.

## Revisit when
Kwame confirms he can license a whole series, including films not on his list. Then switch to setting 1.
