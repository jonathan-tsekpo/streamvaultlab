# Decision notes (ADRs)

An ADR (Architecture Decision Record) is a short note about one decision: what we chose, why, what
else we considered, what it costs if we're wrong, and what would make us change it. These are the
lab's **decision notes**. Every DECISION setting in `pipeline/config.py` is covered by one of them.

ADRs 003–005 are the decisions that shape Kwame's answer. The others are rules that keep the data
clean and the run safe.

| ADR | Decision | Settings in `pipeline/config.py` | Status |
| --- | --- | --- | --- |
| 001 | [Missing or suspicious money figures are treated as "unknown"](001-missing-or-suspicious-money.md) | `zero_budget_is_unknown`, `zero_revenue_is_unknown`, `tiny_money_is_unknown`, `tiny_money_threshold` | Accepted |
| 002 | [Which titles enter the comparison](002-which-titles-are-compared.md) | `released_only`, `exclude_short_films`, `short_film_minutes`, `drop_same_title_and_year`; id rules in `validate.py` | Accepted |
| **003** | [**Any film in a series counts as franchise (studios sell the whole series)**](003-what-counts-as-a-franchise-bundle.md) | `franchise_min_on_list` | Accepted |
| **004** | [**Lead with the typical film's return**](004-which-measure-leads.md) | `HEADLINE_METRIC`, `MIN_GROUP_SIZE` | Accepted |
| **005** | [**Lead with films from 2000 onward**](005-which-time-window-leads.md) | `WINDOW_START_YEAR` | Accepted |
| 006 | [Talent = director and top 3 actors, 2+ films each](006-what-counts-as-talent.md) | `LEAD_CAST_MAX_ORDER`, `TALENT_MIN_FILMS`, `HIT_ROI` | Accepted |
| 007 | [Fast enough for a meeting, stop if results don't add up, no downloaded data in git](007-running-safely-and-repeatably.md) | `TIME_BUDGET_SECONDS`, `MAX_UNUSABLE_SHARE`; `.gitignore` | Accepted |

For a new decision, copy [`template.md`](template.md) and use the next number. To change a decision,
write a new ADR that replaces the old one, rather than editing it.
