# Questions we couldn't ask

Kwame isn't available before the review, so we answered these ourselves. Normally the business
decides what the data means; where we had to decide, we say so, and the linked decision note (ADR)
explains the reasoning and what it costs if we're wrong.

| ID | Finding | Question | Who would normally answer | What we decided | ADR |
| --- | --- | --- | --- | --- | --- |
| Q1 | F5 | Does a revenue of 0 mean the film earned nothing, or that the figure is missing? | Kwame's team | Missing. The film stays in the counts but not in the return figures. None this year. | ADR-001 |
| Q2 | F5 | Same question for a budget of 0. | Kwame's team | Same as Q1. | ADR-001 |
| Q3 | F6 | Is an amount like 12 a typing error or real? | TMDb | A typing error: treated as missing. None this year. | ADR-001 |
| Q4 | F12 | Does a film count as franchise if it's the only film of its series on the list? | Kwame | Yes. The brief says studios sell a series as one bundle, so these films can't be bought alone. But a bundle needs 2+ films on the list to be shortlisted, because one film can't show how the whole bundle performs. | ADR-003 |
| Q5 | F10 | Should films from before 2000 count? | Kwame / Finance (Yaw) | Yes, but the memo leads with 2000 onward and shows all years beside it. | ADR-005 |
| Q6 | F2 | Should we look up the IMDb id on line 95? | Adjoa | No. It's The Dark Knight, which is already on the list (line 2). | ADR-002 |
| Q7 | F7 | Are unreleased films on the list by mistake? | Kwame | Leave them out: no box office to compare. None this year. | ADR-002 |
| Q8 | — | Should we compare the typical film or all the money added up? | Kwame | The typical film leads; the other is shown beside it. | ADR-004 |
| Q9 | — | Which people count as talent, and how many films do they need? | Kwame's negotiators | The director and top 3 actors, with at least 2 films. | ADR-006 |
| Q10 | F4 | Which films did the 5 unknown ids mean (8471293, 8471294, 9412887, 9412888, 7733901)? | Kwame's team | Reported as unusable. We ask for the right ids. They come in pairs, which suggests typing errors. | ADR-007 |
| Q11 | — | How fast must Adjoa's quarterly rerun be, given she sometimes runs it live in a meeting? | Adjoa | 60 seconds for a rerun from the saved data. Measured: about 11 seconds in total; the analysis itself takes under 0.2 seconds even at 5,000 titles. | ADR-007 |
| Q12 | F14 | Which films does each bundle include, beyond those on the list? | The studios | Not answerable from our data. We judge each bundle only by its films on the list and tell Kwame to confirm the full bundle with the studio. | ADR-003 |
