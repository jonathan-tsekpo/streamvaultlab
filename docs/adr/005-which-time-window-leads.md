# ADR-005: The memo leads with films released from 2000 onward; all years are shown beside them

**Status:** Accepted · **Date:** 2026-11-20 · **Deciders:** Jonathan (data engineer)

## Context
The brief asks for the comparison over **all years** and over **2000 onward**. 41 of the 112 films
(37%) were released before 2000: 28 in franchise bundles and 13 standalones (F10). Yaw in Finance
doesn't trust old box office figures, because the market, ticket prices and the way films were
released were very different, and some old totals include later re-releases. Question Q5.

## Decision
`WINDOW_START_YEAR = 2000`. Every result is calculated for both windows. The memo **leads with 2000
onward** and shows all years beside it.

## Alternatives considered
- **Lead with all years.** It uses more films (112 instead of 71), but over a third of them come
  from a market that no longer exists, which Finance would challenge.
- **Remove pre-2000 films completely.** Rejected: we'd lose evidence and hide the fact that the
  typical-film answer is the same in both windows.

| Result | Since 2000 | All years |
| --- | --- | --- |
| Typical film | franchise ahead: 5.05x (59 films) vs 4.49x (12 films) | franchise ahead: 5.53x (87) vs 5.00x (25) |
| All money added up | franchise ahead: 5.10x vs 4.40x | standalone ahead: 5.59x vs 5.52x |

## Consequences
- **Better:** the recommendation is based on the market StreamVault's viewers live in today, and it
  answers Finance's concern before it's raised. Because the typical-film answer is the same in both
  windows, the recommendation is stronger, not weaker.
- **Worse:** the recent standalone group is small (12 films; this is risk #2 in the findings), and
  the list's biggest standalone successes (Jaws, Pulp Fiction, The Good, the Bad and the Ugly) are
  older films, so they don't appear in the headline.

## What survives a rerun at 500 titles
Both windows are always calculated, and the run prints a warning if they give different answers.

## Revisit when
Finance accepts adjusted historical figures (for example, corrected for inflation), or the list
has 30 or more standalone films from 2000 onward.
