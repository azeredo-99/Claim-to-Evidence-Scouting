# Deviations

Every difference between the frozen method and what was actually done. Entries are never edited
after the fact; corrections are new entries.

| Date | Version | What changed | Why | Results seen before the change? |
|---|---|---|---|---|
| 2026-10-11 | method 1.0 | Video evidence closed for the Mendes Moreira case study. C04, C09 and C13 are reported as `UNAVAILABLE`; D2 and D4 are not produced. The pre-registered rules are unchanged: the method already says a match without legitimate full video is reported as missing, not replaced. | The pre-report matches were watched live and cannot be re-watched; no legitimate full-match replay exists for this league (subscription TV only, no official replays). Highlights are excluded by the protocol and were not used as a substitute. | No. No match had been coded and no league data collected. |
| 2026-10-11 | method 1.0 | League data is collected by a private script (not published) instead of by hand: the same pages and fields, one request at a time with pauses, raw responses cached privately. | Less manual work; same source and the same values a person reads on the page. | No. |
| 2026-10-11 | method 1.0 | Match facts (D5: starts, minutes; cards without minute or reason) come from FotMob's match list instead of slgr.gr. | slgr.gr is behind a Cloudflare challenge; it was not bypassed. Card minutes and reasons are therefore unavailable. | No. |
| 2026-10-11 | 1.0 → 1.1 | Omitted statistic rows are read as 0 for players whose stats section exists; the 1.0 reading (missing) is kept as a sensitivity analysis, and the final league verdict is the weakest of both. | The rehearsal snapshot showed that FotMob omits zero-valued rows (no explicit zero for six statistics while players with minutes lacked those rows). Under 1.0 the lowest peers would be dropped, biasing every "low value" claim towards support. | Rehearsal values (2026-10-11, matchday 6) were seen while checking the file format; no claim had an evaluable verdict (all `INSUFFICIENT_DATA` at that date). |
