# Findings log

What we found when we checked Kwame's candidate list and the film data from TMDb, how we detected
it, how we handled it, and how it affects the recommendation. All numbers come from the latest run
(`out/summary.md`, TMDb data from 20 November 2026). The detail behind each number is in `out/tables/`.

**Key terms:** a film's *return* is its box office divided by its budget (5x = earned five times its
cost). The *typical film* is the middle film when a group is ranked by return. *All money added up*
is a group's total box office divided by its total budget.

## Top 3 risks to the recommendation

Ranked by how much each finding could change the answer, or how confident Kwame can be in it.

| Rank | ID | What we saw | How it affects the answer | Verdict | Decision |
| --- | --- | --- | --- | --- | --- |
| 1 | F12 | 9 films are the only film from their series on the list (Jaws, The Lion King, The Silence of the Lambs, Ghostbusters, Blade Runner, The Incredibles, Monsters, Inc., The Smurfs, Mad Max: Fury Road). Whether they count as franchise or standalone is a choice we have to make. | **It can flip one result.** All money added up, all years: franchises lead 5.58x to 4.85x when these 9 count as franchise (our choice); standalones would lead 5.59x to 5.52x if they counted as standalone. The typical-film result favours franchises either way. | Legitimate, but needs a definition | Count them as franchise, because the brief says studios sell a series only as a whole bundle (ADR-003). Don't shortlist bundles with only one film on the list. |
| 2 | — | The groups are very uneven: 96 franchise films against 16 standalones, and only **8 standalones since 2000** (against 63 franchise). | The recent typical standalone figure (3.85x) is the midpoint of just 8 films (between The Departed, 3.24x, and Memento, 4.45x). Adding or swapping one or two films could move it a lot. This doesn't change which way the answer points, but it limits how sure Kwame can be about standalones. | Legitimate (it's the list Kwame sent) | Show the number of films next to every figure, and present the result as a clear lean, not a certainty (ADR-004). |
| 3 | F10 | 41 films (37%) were released before 2000: 33 franchise, 8 standalone. Finance distrusts old box office figures. | Leaving them out shrinks the franchise lead on the typical film by a third (from 1.78 to 1.21), but **franchises still lead on every measure in both windows**, so the recommendation doesn't change between them. | Different population (an older market) | Lead with 2000 onward and show all years beside it (ADR-005). |

**Not ranked, but reported to Kwame** (we can't measure them with this data, so they're in the memo
under "What we couldn't check"):
- **F14, bundles include films that aren't on the list.** We only see the listed films of each series,
  so we can't see the weak sequels his team worries about. A bundle's real performance could be lower
  than our figures.
- **The list contains only famous, successful films.** 75% of standalones and 98% of franchise films
  earned at least twice their budget, far more than films in general, so the answer applies to
  well-known titles like these.

## All findings

**Verdicts:** *Defect* = the data is wrong. *Legitimate* = it looks unusual but is correct.
*Different population* = correct, but not directly comparable. *None found* = we check for it, but
nothing turned up this year. *Limit* = a real gap we can't measure with this data.

| ID | What we saw | How we detected it | Verdict | Decision | Handled in | Shown by | Decided in |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | 6 lines repeat an id already on the list: lines 43, 60, 90, 91, 94, 102 repeat lines 40, 27, 55, 2, 80, 8 | Compared each id (spaces and leading zeros removed) with all earlier lines | Defect (in the list) | Analyse each film once, from its first line; set the repeats aside. No film is lost. | `validate.py` | `id_quarantine.csv` | ADR-002 |
| F2 | 3 lines aren't TMDb ids: `-1` (line 30), `N/A` (line 111), `tt0468569` (line 95, the IMDb id of The Dark Knight, already on the list at line 2) | Checked that every line is a whole number | Defect (in the list) | Set aside, don't try to repair. Nothing is lost. | `validate.py` | `id_quarantine.csv` | ADR-002 |
| F3 | 1 blank line (line 69) | Read every line of the file as text, including blank lines | Defect (in the list) | Set aside, so all 127 lines are still accounted for. | `extract.py`, `validate.py` | `id_quarantine.csv` | ADR-002 |
| F4 | 5 ids don't exist on TMDb: 8471293, 8471294, 9412887, 9412888, 7733901 (lines 18, 73, 35, 93, 99). They come in consecutive pairs, which suggests typing errors. | TMDb answered "not found" (404) for both details and credits | Defect (in the list) | Report them as unusable; ask Kwame's team for the correct ids (Q10). | `extract.py` | `id_account.csv` | ADR-007 |
| F5 | Films with a budget or revenue of 0: none | Counted films with 0 in either field | None found | A 0 would be treated as "unknown". | `transform.py` | `findings.csv` | ADR-001 |
| F6 | Amounts above $0 but under $1,000: none | Counted films with either figure between $1 and $999 | None found | Would be treated as "unknown" (likely a typing error). | `transform.py` | `findings.csv` | ADR-001 |
| F7 | Unreleased films: none | Checked each film's release status | None found | Would be left out (no box office yet). | `validate.py` | `film_quarantine.csv` | ADR-002 |
| F8 | Short films (under 40 minutes) or no running time: none | Checked each film's running time | None found | Would be left out (a different product). | `validate.py` | `film_quarantine.csv` | ADR-002 |
| F9 | The same title and year under two ids: none | Compared titles and years, ignoring capitals and spaces | None found | Would be counted once. | `validate.py` | `film_quarantine.csv` | ADR-002 |
| F10 | 41 films (37%) released before 2000: 33 franchise, 8 standalone | Counted films by release year | Different population | Show both windows; lead with 2000 onward (risk #3). | `analysis.py` | `kpis.csv` | ADR-005 |
| F11 | 4 films with extreme returns (32x to 70x), all before 2000: Star Wars, The Godfather, Jaws (franchise) and The Good, the Bad and the Ugly (standalone) | Flagged returns far outside the range of the other films | Legitimate (real hits) | Keep them. Lead with the typical film, which they can't distort. | `diagnose.py` | `findings.csv` | ADR-004 |
| F12 | 9 films are the only film of their series on the list | Counted how many films of each series are on the list | Legitimate, needs a definition | Count them as franchise; don't shortlist one-film bundles (risk #1). | `transform.py`, `analysis.py` | `fact_films.csv`, `sensitivity.csv` | ADR-003 |
| F13 | Films with no cast or director listed: none (0 without cast, 0 without director) | Checked that every film has cast and director entries | None found | Would stay in the comparison but couldn't appear in the talent tables. | `transform.py` | `cast.csv`, `directors.csv` | ADR-006 |
| F14 | Bundles include films that aren't on the list (at least the sequels of the 9 lone films above) | The 9 lone films belong to series whose other films aren't on the list. The two data sources we were given (film details and credits) don't list a series' full contents. | Limit | Judge each bundle only by its films on the list; tell Kwame to confirm the full bundle with the studio (Q12). | `analysis.py` | `franchise_candidates.csv` (`films_on_list`) | ADR-003 |

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
them (96%). The other 5 aren't real TMDb ids, so we can't tell which films were intended. With only
8 recent standalones, those 5 could matter if any of them is a standalone. The bad lines cost nothing
else: the IMDb id on line 95 is a film that's already on the list.
