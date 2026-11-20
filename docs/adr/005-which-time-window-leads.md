# ADR-005: The memo leads with films released from 2000 onward; all years are shown beside them

**Status:** Accepted · **Date:** 2026-11-20 · **Deciders:** Jonathan (data engineer)

## Context
The brief asks for the comparison over **all years** and over **2000 onward**, and says to state
loudly if the recommendation changes between them. 41 of the 112 films (37%) were released before
2000: 33 franchise and 8 standalone (F10). Yaw in Finance distrusts old box office figures because of
inflation, currency reporting and how box office used to be reported. Question Q5.

## Decision
`WINDOW_START_YEAR = 2000`. Every result is calculated for both windows. The memo **leads with 2000
onward** and shows all years beside it.

## Alternatives considered
- **Lead with all years.** It uses more films (112 instead of 71), but over a third of them come from
  a market Finance will challenge.
- **Remove pre-2000 films completely.** Rejected: we'd lose evidence and hide the fact that the answer
  is the same in both windows.

| Result | Since 2000 | All years |
| --- | --- | --- |
| Typical film | franchise ahead: 5.05x (63 films) vs 3.85x (8 films) | franchise ahead: 5.62x (96) vs 3.85x (16) |
| All money added up | franchise ahead: 5.08x vs 4.24x | franchise ahead: 5.58x vs 4.85x |

**The recommendation doesn't change between the windows.** Old films make the franchise lead look
bigger (1.78 over all years against 1.21 since 2000, on the typical film), but they don't change who leads.

## Consequences
- **Better:** the recommendation rests on today's market and answers Finance's concern before it's
  raised. Because both windows agree, the recommendation is stronger.
- **Worse:** only 8 standalone films are from 2000 onward (risk #2 in the findings), and the biggest
  standalone successes on the list (The Good, the Bad and the Ugly, Pulp Fiction) are older, so they
  don't appear in the headline.

## What survives a rerun at 500 titles
Both windows are always calculated, and the run prints a warning if they give different answers.

## Revisit when
Finance accepts adjusted historical figures (for example, corrected for inflation), or the list has
30 or more standalone films from 2000 onward.
