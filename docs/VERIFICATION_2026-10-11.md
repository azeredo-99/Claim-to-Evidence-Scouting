# Source verification — 2026-10-11

Done manually in a browser before the pre-registration. **Only labels and page structure were
recorded, never statistical values.**

## FotMob

- Reference player: Stefanos Stroungis, centre-back, Kalamata
  (<https://www.fotmob.com/players/900344/stefanos-stroungis>). Also consulted: the subject's page
  (<https://www.fotmob.com/players/947883/ahmad-mendes-moreira>), the squad page
  (<https://www.fotmob.com/teams/1585/squad/kalamata>) and team stats
  (<https://www.fotmob.com/teams/1585/stats/kalamata/teams>).
- The interface was switched from Portuguese to English before reading labels.
- "Season performance" shows totals by default, with a Per 90 toggle; both modes list the same
  labels.
- Labels found (current season): `Minutes played`, `Chances created`, `Expected assists (xA)`,
  `Non-penalty xG`, `Touches`, `Touches in opposition box`, `Dispossessed`, `Fouls won`, `Tackles`,
  `Interceptions` (centre-back), goals, assists and cards.
- `Tackles won` appears only in the page's translation strings, not as a statistic row; the page
  does not say whether `Tackles` counts attempts or only won tackles.
- `Interceptions` (and `Blocked shots`) are absent from the 2026/27 data of the subject and of
  another attacking player, but present for the centre-back. The league has an
  `Interceptions per 90` list. Cause not confirmed.
- `Average possession`: team stats; the league list covers all 14 teams.
- Positions on the squad page: `Attacking Midfielder`, `Left Winger`, `Right Winger`,
  `Left Midfielder`, `Right Midfielder`; a player may list several.
- No split of chances created by situation (the shot map's "Situation" filter covers shots only).
- Subject's past seasons: no xA, xG or non-penalty xG in any. Detailed lists (chances created,
  touches, dispossessed, fouls won, tackles) in 2022/23 Super League, 2020/21 Eerste Divisie and
  2018/19 Eredivisie; only goals, assists, minutes and cards in 2023/24, 2019/20 and 2018/19
  Eerste Divisie; only goals in 2025/26 and 2024/25; an empty section in 2021/22. The 2025/26 and
  2024/25 readings come from the page data, read twice; a consent banner prevented a visual check.

## slgr.gr

- Match sheets checked: 2627014, 2627002, 2627016, 2627023, 2627032, 2627036, 2627037
  (<https://www.slgr.gr/en/game/2627014/> etc.).
- Squads tab: starting XI (11) and substitutes. Game flow: substitutions and cards with minutes
  (including `90+4'`), icons `Yellow card`, `Red card`, `Sent off(2nd yellow card)`.
  Players statistics tab: `Time played`, not yet filled one day after a match.
- Calendar (<https://www.slgr.gr/en/schedule/>), regular season 2026-27: PAOK–Kalamata 12/10
  (round 6), Kalamata–OFI 18/10 (round 7), Olympiacos–Kalamata 25/10 (round 8). Round 10 is played
  on 7–8/11, last match on 08/11. Atromitos–AEK (round 7) had no date. Kick-off times differ
  between list and match page for some games; dates agree.
- The site's terms of use were not read.

## Video

No free, legitimate full-match source was found (broadcasts are subscription TV). The pilot and all
coding are done by the author watching legitimately accessed matches.

## Decisions taken from this check (before the freeze)

| Item | Decision |
|---|---|
| Interceptions missing for some players | C08 main metric is `Tackles` per 90; tackles + interceptions is a sensitivity variant where available; an absent row is missing, never zero |
| Tackles label | `Tackles`, with the limitation that attempts vs won is not stated |
| Peer positions | First listed position ∈ {AM, LW, RW, LM, RM} |
| v1 cut-off | `last_match_date` 2026-11-08, snapshot 2026-11-10; postponed matches count only if played by then |
| Video sample | Fixed explicitly: Aris, Volos, Panathinaikos (pre-report); PAOK 12/10, OFI 18/10, Olympiacos 25/10 |
| Protocol clarifications | Pilot codes the observed team's left-sided attacker; throw-ins are not receptions; added-time clock example; headed passes count as chances created; back-line changes do not change the runner |
