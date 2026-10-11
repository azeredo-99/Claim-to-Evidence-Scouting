# Field check, official calendar and video pilot — 2026-10-11

Record of the checks listed in `DATA_SOURCES.md` ("Field check"). **Labels and existence only: no
statistical values were recorded.** Everything below was consulted on 2026-10-11 in a browser
with the FotMob interface set to English.

Status words used:

- **available** — the label was seen on the page and section given.
- **not shown** — the page and section were checked and the label is not there; this does not
  mean the provider lacks the field elsewhere.
- **not confirmed** — could not be established either way on the pages consulted.

## A. FotMob

### Pages consulted

| Page | URL |
|---|---|
| Reference centre-back: Stefanos Stroungis (Kalamata, primary position "Center-Back") | https://www.fotmob.com/players/900344/stefanos-stroungis |
| Subject: Ahmad Mendes Moreira (Kalamata) | https://www.fotmob.com/players/947883/ahmad-mendes-moreira |
| Kalamata squad | https://www.fotmob.com/teams/1585/squad/kalamata |
| Kalamata team stats | https://www.fotmob.com/teams/1585/stats/kalamata/teams |
| League team list, Average possession | https://www.fotmob.com/leagues/135/stats/season/44734/teams/possession_percentage_team/team/1585/kalamata-teams |
| League player stats (category list) | https://www.fotmob.com/leagues/135/stats/super-league-1 |
| Label-only comparison: Josete Miranda (Kalamata, Left Winger) | https://www.fotmob.com/players/627510/josete-miranda |

The reference player is a centre-back of the same team, so he can never be a peer.

### Fields

Player page section = "Season performance" (sub-headings Shooting, Passing, Possession, Defending,
Discipline), with a **Total / Per 90** toggle. **Total is selected by default**; the list of
labels is identical in both modes.

| Field wanted | Exists? | Exact label | Page / section | Notes |
|---|---|---|---|---|
| Season tab, totals | available | Player page: competition "Super League" + season "2026/2027" (heading "Super League 2026/2027"); league and team pages: "Super League 1 2026/2027" | Player page, season selector; team stats selector | The competition name differs between player pages and league/team pages. Values default to "Total". |
| Minutes played | available | `Minutes played` | Player page, season summary card; also heading "Minutes played: …" of Season performance | |
| Chances created | available | `Chances created` | Season performance › Passing | Also a league category "Chances created". |
| Expected assists (xA) | available | `Expected assists (xA)` | Season performance › Passing | League categories "Expected assists (xA)" and "xA per 90". |
| Non-penalty xG | available | `Non-penalty xG` | Season performance › Shooting | Not a league category. |
| Touches | available | `Touches` | Season performance › Possession | Also "Touches: …" above the heatmap. |
| Touches in opposition box | available | `Touches in opposition box` | Season performance › Possession | |
| Dispossessed | available | `Dispossessed` | Season performance › Possession | |
| Fouls won | available | `Fouls won` | Season performance › Possession | |
| Tackles | available | `Tackles` (not "Tackles won") | Season performance › Defending | "Tackles won" and "Tackles attempted" exist only as interface translation strings embedded in the page, not as a season-performance row. Whether `Tackles` counts attempts or successful tackles is **not stated** on the page. League category: "Tackles per 90"; team stats: "Tackles per match". |
| Interceptions | available on the centre-back page; **not shown** on the subject's 2026/27 page | `Interceptions` | Season performance › Defending (centre-back) | Also absent from Josete Miranda's 2026/27 page; present on the subject's 2022/23 page. The row is missing from the page data, not only hidden. Reason not confirmed (possibly omitted when zero, possibly position-dependent). League category: "Interceptions per 90"; team stats: "Interceptions per match". See proposal P1. |
| Assists, goals, yellow cards | available | `Assists`, `Goals`, `Yellow cards` | Season performance; summary card has Goals and Assists | |
| Team average possession | available | `Average possession` | Team stats › Top stats (team row shown with league leaders); full list of the 14 teams on the league "Average possession" page | Selector reads "Super League 1 2026/2027". |
| Position labels on squad pages | available | Column `Position` shows abbreviations; hover title shows the full label: `Attacking Midfielder` (AM), `Left Winger` (LW), `Right Winger` (RW), also `Left Midfielder` (LM), `Right Midfielder` (RM), `Central Midfielder` (CM), `Striker` (ST) | Team › Squad | Players may carry several positions (e.g. "LM, LW", "RW, ST"). Some players have only a group label (`Defender`, `Attacker`). The subject is listed as `LW` / "Left Winger". The labels in `player.yaml` (`Attacking Midfielder`, `Left Winger`, `Right Winger`) match the interface exactly. See proposal P3. |
| Split of chances created by situation | not shown | — | Season performance; league category list | The season shot map has a "Situation" filter (Regular play, Fast break, Set piece, From corner, Free kick…), but it applies to the player's **shots**, not to chances created. |

Other labels present in Season performance (2026/27, subject's page): Expected goals (xG),
xG on target (xGOT), Shots, Shots on target, Headed shots, Successful passes, Successful passes %,
Accurate long balls, Accurate long balls %, Big chances created, Successful crosses, Successful
crosses %, Successful dribbles, Successful dribbles %, Duels won, Duels won %, Aerial duels won,
Aerial duels won %, Defensive contributions, Fouls committed, Recoveries, Possession won final 3rd,
Dribbled past, Clearances, Clean sheets, Goals conceded while on pitch, xG against while on pitch,
Red cards. The centre-back page additionally shows Interceptions and Blocked shots, and does not
show Big chances created, Successful crosses, Successful dribbles or Possession won final 3rd.

### Subject's past seasons (D6) — labels visible, no values

Season selector of the subject's page, every entry checked. "Card" = the season summary card;
"Season performance" = the detailed section.

| Season | Competition | Card labels | Season performance labels |
|---|---|---|---|
| 2026/2027 | Super League | Goals, Assists, Started, Matches, Minutes played, Rating | full list above (no Interceptions, no Blocked shots) |
| 2026/2027 | Cup Group Stage | none | section not shown |
| 2025/2026 | Super League 2 Grp. B | Goals | section not shown |
| 2024/2025 | Super League 2 Grp. B | Goals | section not shown |
| 2023/2024 | 1. Division | Goals, Assists, Minutes played, Yellow cards, Red cards | section not shown |
| 2022/2023 | Super League | Goals, Assists, Rating, Matches, Started, Minutes played | Goals, Shots, Shots on target, Assists, Successful passes, Successful passes %, Accurate long balls, Accurate long balls %, Chances created, Big chances created, Successful crosses, Successful crosses %, Successful dribbles, Successful dribbles %, Duels won, Duels won %, Aerial duels won, Aerial duels won %, Touches, Touches in opposition box, Dispossessed, Fouls won, Defensive contributions, Tackles, Interceptions, Blocked shots, Fouls committed, Penalties conceded, Recoveries, Possession won final 3rd, Dribbled past, Clean sheets, Goals conceded while on pitch, Yellow cards, Red cards |
| 2021/2022 | Super League | none | heading and Total/Per 90 toggle shown, **no rows** |
| 2020/2021 | Eerste Divisie | Goals, Assists, Rating, Matches, Started, Minutes played | as 2022/23 without Penalties conceded |
| 2019/2020 | Eerste Divisie | Goals, Assists, Minutes played, Yellow cards, Red cards | section not shown |
| 2018/2019 | Eredivisie | Goals, Assists, Rating, Matches, Started, Minutes played | as 2020/21 without Interceptions and Blocked shots |
| 2018/2019 | Eerste Divisie | Goals, Assists, Minutes played, Yellow cards, Red cards | section not shown |

For items 2–5 of the field check: **no past season shows Expected assists (xA), Non-penalty xG
or Expected goals (xG)**. Minutes played is shown in every past season except 2025/26, 2024/25 and
2021/22. Chances created is shown in 2022/23, 2020/21 and 2018/19 (Eredivisie) only.

The 2025/26 and 2024/25 cards were read from the page DOM twice with the same result; they were
not checked visually because a consent dialog covered the page (it was left unanswered).

### Limitations

- The browser locale redirected FotMob to Portuguese (`/pt-PT/`); the locale cookie was set to
  English before recording labels. Portuguese labels differ (e.g. "Extremo esquerdo").
- Labels were checked on 2026-10-11 only; FotMob can change its interface.
- The reason Interceptions is missing for some players is not established.

## B. slgr.gr

### Match sheets

Each sheet has four tabs: Game flow (`/en/game/<id>/`), Squads (`…/squads/`), Statistics,
Players statistics (`…/players-stats/`).

| URL | Match | What was verified |
|---|---|---|
| https://www.slgr.gr/en/game/2627014/ | Panetolikos–Kalamata, Matchday 2, 29/08/2026 | Game flow: every event has a minute (added time as `45+1'`, `90+4'`) and an icon titled `Yellow card`, `Substitution in` / `Substitution out`, `goal`, etc. Squads: per team a table headed with the team name (11 players, starting line-up) and a `Substitutes` table; positions only as GOALKEEPER / DEFENDER / MIDFIELDER / FORWARD. Players statistics: column `Time played`. |
| https://www.slgr.gr/en/game/2627002/ | Kalamata–Aris, Matchday 1 | Same structure; a `Red card` event with its minute. |
| https://www.slgr.gr/en/game/2627016/ | Atromitos–Kalamata, Matchday 3 | Same structure; a `Sent off(2nd yellow card)` event with its minute. |
| https://www.slgr.gr/en/game/2627023/ | Kalamata–Volos, Matchday 4 | Same structure (11 + substitutes; substitutions and cards with minutes; Time played). |
| https://www.slgr.gr/en/game/2627032/ | Kalamata–Panathinaikos, Matchday 5 | Same structure. |
| https://www.slgr.gr/en/game/2627036/ | AEK–OFI, Matchday 6 | Same structure. |
| https://www.slgr.gr/en/game/2627037/ | Asteras Aktor–Atromitos, Matchday 6 (played 10/10) | Game flow and Squads present; **Players statistics without "Time played"** one day after the match. |

Conclusion: starting line-ups, substitution minutes, and cards **with minutes** (yellow, red,
second yellow) can be read from the official sheets. The team of each Game-flow event is given by
its column (home left, away right), not by text. The Squads tab does not show substitution icons.

### Official calendar

Season **2026-2027**, competition **Stoiximan Super League** (regular season, Matchdays 1–26),
pages `https://www.slgr.gr/en/schedule/25/158/2627NN/` (NN = matchday).

| Date | Calendar | Match | Matchday |
|---|---|---|---|
| 12/10/2026 | confirmed | P.A.O.K.–Kalamata (`/en/game/2627041/`) | 6 |
| 18/10/2026 | confirmed | Kalamata–O.F.I. (`/en/game/2627044/`) | 7 |
| 25/10/2026 | confirmed | Olympiacos–Kalamata (`/en/game/2627054/`) | 8 |

**Matchday 10** (`/en/schedule/25/158/262710/`) is scheduled on 07/11 and 08/11/2026; its last
match is Olympiacos–P.A.O.K., 08/11/2026 (`/en/game/2627068/`). Kalamata play Asteras Aktor–Kalamata
on 08/11.

Caveats:

- **Matchday 7, Atromitos–AEK (`/en/game/2627043/`): "The date has not yet been set."** Until it is
  fixed, "all league matches completed through round 10" cannot be dated, even though Matchday 10
  itself ends on 08/11.
- Kick-off times differ between the schedule list and the match-page title for some matches
  (e.g. Matchday 2: 19:30 vs 21:30); the time zone is not stated. Dates were consistent; no match
  in the table is close enough to midnight for the date to change.
- Also seen: Matchday 15 ends 20/12/2026 (O.F.I.–Kalamata that day); Matchday 16 starts 09/01/2027.

The site's terms of service were not reviewed in this check.

## C. Video pilot (20 minutes, another team) — not carried out

Guide and protocol located: `docs/CODING_QUICK_REFERENCE.md` and `docs/TAGGING_PROTOCOL.md`
(version 1.0-rc1); schema in `src/c2e/contracts.py` (`validate_tagging`).

No events were coded and no CSV was produced, for two independent reasons:

1. **Source.** The broadcasters listed on the official schedule (NS PRIME, MS1L, ΣΠΟΡ FM TV) are
   TV/subscription channels. No free, legitimate full-match replay was found; highlights are
   excluded by the protocol. Watching a subscription stream would require signing in to the
   user's account, which was not done.
2. **Method.** The assistant's browser returns still screenshots, not continuous video. The
   protocol depends on continuous observation (5 s possession, 8 s run window, end moment ±1 s,
   distance at a moment). Coding from sampled frames would not follow the protocol and would amount
   to simulated data.

The pilot therefore has to be coded by a human coder. Questions to watch during it are listed
under D (items P5–P10).

## D. Proposed changes — pending approval (nothing below has been applied)

From the field check:

- **P1 — Interceptions for C08.** The row is missing from some players' 2026/27 pages, including
  the subject's. Options: (a) use the league list "Interceptions per 90" for every player;
  (b) treat a missing row as missing data and report C08 as `unavailable`; (c) treat it as zero
  only if FotMob documents that behaviour. Not decided.
- **P2 — Tackles label.** `config/metrics.yaml` has "FotMob tackles label (confirm)"; the label is
  `Tackles`. Its definition (attempted vs won) is not stated, while `metrics.yaml` defines the metric
  as "successful defensive interventions". Proposed: set `source_label` to FotMob "Tackles" and add
  a limitation that FotMob does not state whether failed tackles are included.
- **P3 — Peer positions.** Labels match `player.yaml`. To decide: whether a player counts as a peer
  by **any** listed position or by the **first** one, and whether `Left Midfielder` / `Right
  Midfielder` are included.
- **P4 — Snapshot v1 date.** Matchday 10 ends 08/11/2026, but a Matchday 7 match has no date.
  Decide whether v1 waits for that match or is defined as "Matchday 10 played".

From reading the protocol for the pilot (not from video):

- **P5 — Pilot subject.** The protocol is written around "the player" and "his team". For a pilot
  on another team it does not say who the subject is (proposal: that team's left-sided wide player)
  nor where the pilot files live (the subject's `tagging/` folder with `sample = pilot`, or a
  separate folder).
- **P6 — Throw-ins.** `chance_created` treats throw-ins as open play; `reception` excludes
  "receptions from set pieces" without saying whether a throw-in is one.
- **P7 — Added-time clock.** Broadcasts often show `45:00 +1:30` rather than `46:30`. The rule
  for converting is implicit.
- **P8 — Chance created by a header or flick-on.** "Pass or cross" does not say whether headed
  passes count.
- **P9 — Pilot length vs `minutes_played`.** `matches.csv` needs minutes from the official sheet;
  for a 20-minute pilot the coded interval is not recorded anywhere in the schema.
- **P10 — Opponent changes shape during a possession.** The runner is fixed at the start of the
  possession; the protocol does not say what happens if the right-most defender changes.
