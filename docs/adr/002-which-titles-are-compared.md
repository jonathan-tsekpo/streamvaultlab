# ADR-002: Which titles enter the comparison

**Status:** Accepted · **Date:** 2026-11-20 · **Deciders:** Jonathan (data engineer)

## Context
Kwame's list has 127 lines. A fair comparison needs every line to be a real, released, full-length
film, counted once. We found:
- **3 lines that aren't TMDb ids** (F2): `-1` (line 30), `N/A` (line 111) and `tt0468569` (line 95).
  The last one is an IMDb id (a different website's numbering) for *The Dark Knight*, which is
  already on the list as TMDb id 155 (line 2).
- **6 repeated lines** (F1) and **1 blank line** (F3).
- **No** unreleased films, short films or films listed twice under different ids (F7–F9).

Questions Q6 and Q7.

## Decision
1. **Only a whole number counts as a TMDb id.** Anything else is set aside with the reason
   "not a TMDb id". We don't try to repair it.
2. **A repeated id is analysed once**, from its first line. Repeats are set aside as "duplicate line".
3. **Unreleased films are left out** (`RULES["released_only"] = True`), because they have no box office yet.
4. **Short films under 40 minutes are left out** (`RULES["exclude_short_films"] = True`,
   `RULES["short_film_minutes"] = 40`), because they are a different product from feature films.
5. **The same title and year under two ids counts once** (`RULES["drop_same_title_and_year"] = True`).

Every line that is set aside is listed with its line number and reason, so all 127 lines are accounted for.

## Alternatives considered
- **Look up IMDb ids on TMDb.** Rejected for now: it needs extra code for a single line, and here it
  would only find a film we already have.
- **Guess fixes (e.g. read `550.0` as 550).** Rejected: a wrong guess would quietly add the wrong
  film's money to the analysis.
- **Keep unreleased or short films.** Rejected: they can't be compared fairly with released features.

## Consequences
Nothing is guessed, every line is explained, and no real film is lost this year. If a future list
has many IMDb ids, those films would be left out until the list is corrected.

## What survives a rerun at 500 titles
The rules run on their own. Set-aside lines and films are listed in `id_quarantine.csv` and
`film_quarantine.csv`, so Adjoa can send them back to Kwame's team to correct.

## Revisit when
A list arrives with many IMDb ids (then looking them up is worth the code), or Kwame wants upcoming
films assessed (that needs a different method).
