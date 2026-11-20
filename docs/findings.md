# Findings log

What we found when we checked Kwame's candidate list and the film data from TMDb, how we handled
each finding, and how it affects the recommendation. All numbers come from the latest run
(`out/summary.md`, TMDb data from 20 November 2026). The detail behind each number is in `out/tables/`.

**Key terms:** a film's *return* is its box office divided by its budget (5x = earned five times its
cost). The *typical film* is the middle film when a group is ranked by return. *All money added up*
is a group's total box office divided by its total budget.

## Top 3 risks to the recommendation

Ranked by how much each finding could change the answer, or how confident Kwame can be in it.

| Rank | ID | What we saw | How it affects the answer | Verdict | Decision |
| --- | --- | --- | --- | --- | --- |
| 1 | F12 | 9 films are the only film from their series on the list (Jaws, The Lion King, The Silence of the Lambs, Ghostbusters, Blade Runner, The Incredibles, Monsters, Inc., The Smurfs, Mad Max: Fury Road). Whether they count as franchise or standalone is a choice we have to make. | **It flips one result.** All money added up, all years: franchises lead 5.58x to 4.85x if these 9 count as franchise; standalones lead 5.59x to 5.52x if they don't. The typical-film result favours franchises either way, but the lead shrinks from 1.78 to 0.53. | Legitimate, but needs a definition | A franchise bundle needs 2+ films of the series on the list, because that's what Kwame would buy (ADR-003). The memo explains that the other choice flips the result. |
| 2 | — | The groups are uneven: 87 franchise films against 25 standalones, and only **12 standalones since 2000** (against 59 franchise). | The recent comparison (typical film 5.05x vs 4.49x) rests on just 12 standalone films. Swapping one or two of them could change it. This doesn't change which way the answer points, but it limits how sure Kwame can be. | Legitimate (it's the list Kwame sent) | Show the number of films next to every figure, and present the result as a lean, not a certainty (ADR-004). |
| 3 | F10 | 41 films (37%) were released before 2000: 28 franchise, 13 standalone. Finance doesn't trust old box office figures. | Typical film: franchises lead in both windows (lead of 0.53 over all years, 0.56 since 2000). All money added up: **the leader changes with the window**, standalone over all years (5.59x vs 5.52x) but franchise since 2000 (5.10x vs 4.40x), because of old standalone hits such as Jaws (67x) and The Good, the Bad and the Ugly (32x). | Different population (an older market) | Lead with 2000 onward and show all years beside it (ADR-005). |

**Not ranked, but reported:** the list contains only famous, successful films (80% of standalones
and 99% of franchise films earned at least twice their budget, far more than films in general). This
limits how far the answer applies, but we can't measure or correct it with this data, so it's in the
memo under "What we couldn't check".

## All findings

**Verdicts:** *Defect* = the data is wrong. *Legitimate* = it looks unusual but is correct.
*Different population* = correct, but not directly comparable. *None found* = we check for it, but
nothing turned up this year.

| ID | What we saw | Verdict | Decision | Handled in | Shown by | Decided in |
| --- | --- | --- | --- | --- | --- | --- |
| F1 | 6 lines repeat an id already on the list: lines 43, 60, 90, 91, 94, 102 repeat lines 40, 27, 55, 2, 80, 8 | Defect (in the list) | Analyse each film once, from its first line; set the repeats aside. No film is lost. | `validate.py` | `id_quarantine.csv` | ADR-002 |
| F2 | 3 lines aren't TMDb ids: `-1` (line 30), `N/A` (line 111), `tt0468569` (line 95). The last is the IMDb id of The Dark Knight, which is already on the list (line 2). | Defect (in the list) | Set aside, don't try to repair. Nothing is lost. | `validate.py` | `id_quarantine.csv` | ADR-002 |
| F3 | 1 blank line (line 69) | Defect (in the list) | Set aside, so all 127 lines are still accounted for. | `extract.py`, `validate.py` | `id_quarantine.csv` | ADR-002 |
| F4 | 5 ids don't exist on TMDb: 8471293, 8471294, 9412887, 9412888, 7733901 (lines 18, 73, 35, 93, 99). They come in consecutive pairs, which suggests typing errors. | Defect (in the list) | Report them as unusable and ask Kwame's team for the correct ids (Q10). | `extract.py` | `id_account.csv` | ADR-007 |
| F5 | Films with a budget or revenue of 0: none | None found | A 0 would be treated as "unknown". | `transform.py` | `findings.csv` | ADR-001 |
| F6 | Amounts above $0 but under $1,000: none | None found | Would be treated as "unknown" (likely a typing error). | `transform.py` | `findings.csv` | ADR-001 |
| F7 | Unreleased films: none | None found | Would be left out (no box office yet). | `validate.py` | `film_quarantine.csv` | ADR-002 |
| F8 | Short films (under 40 minutes) or films with no running time: none | None found | Would be left out (a different product). | `validate.py` | `film_quarantine.csv` | ADR-002 |
| F9 | The same title and year under two ids: none | None found | Would be counted once. | `validate.py` | `film_quarantine.csv` | ADR-002 |
| F10 | 41 films (37%) released before 2000: 28 franchise, 13 standalone | Different population | Show both windows; lead with 2000 onward (risk #3). | `analysis.py` | `kpis.csv` | ADR-005 |
| F11 | 4 films with extreme returns, all before 2000: Star Wars, The Godfather, The Good, the Bad and the Ugly, Jaws | Legitimate (real hits) | Keep them. Lead with the typical film, which they can't distort. | `diagnose.py` | `findings.csv` | ADR-004 |
| F12 | 9 series have only one film on the list | Legitimate, needs a definition | Count those films as standalone (risk #1). | `transform.py` | `fact_films.csv`, `sensitivity.csv` | ADR-003 |
| F13 | Films with no cast or director listed: none (0 without cast, 0 without director) | None found | Would stay in the comparison but couldn't appear in the talent tables. | `transform.py` | `cast.csv`, `directors.csv` | ADR-006 |
A finding of "none" still matters: it tells Adjoa the check exists and that nothing was wrong this year.

## Where every line of the list went

| Outcome | Lines |
| --- | --- |
| Analysed | 112 |
| Repeated line (the film is analysed from its first line) | 6 |
| Id not found on TMDb | 5 |
| Not a TMDb id | 3 |
| Blank line | 1 |
| **Total** | **127** |

**What this means for Kwame:** the list contains 117 different usable ids, and we analysed 112 of
them (96%). The other 5 aren't real TMDb ids, so we can't tell which films were intended. The bad
lines cost nothing else: the IMDb id on line 95 is a film that's already on the list.
