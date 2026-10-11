# Collecting a snapshot

How to fill the CSVs for a league snapshot by hand. Copy `templates/` into a **private** folder
(for example `private/v1/`, which git ignores) and fill one file at a time. Never commit it.

## When

On the `snapshot_date` of `players/<id>/player.yaml` (v1: 2026-11-10), after `last_match_date`
and before the next round starts. Write that date in every `retrieved_at` cell.

## `league_snapshot.csv` — one row per player

Who: the subject, every player whose **first listed position** on his club's FotMob squad page is
one of the configured peer positions, and every team-mate of the subject (for D3). Players below
the minimum minutes can be included; the engine filters them.

| Column | Where on FotMob | Notes |
|---|---|---|
| `player_id` | Number in the player's URL (`/players/947883/...`) | |
| `player_name`, `team` | Player page | `team` as written in `teams.csv` |
| `position` | Squad page, first listed position | Exact label, e.g. `Left Winger` |
| `minutes` | Season performance, `Minutes played` | Super League 1 tab, **Total** view |
| `assists`, `goals` | Season performance | |
| `chances_created`, `xa` | Passing: `Chances created`, `Expected assists (xA)` | |
| `npxg` | Shooting: `Non-penalty xG` | |
| `touches`, `touches_opp_box`, `dispossessed`, `fouls_won` | Possession | |
| `tackles`, `interceptions` | Defending: `Tackles`, `Interceptions` | |
| `source`, `url` | `FotMob`, the player page URL | |

**Rules**

- Always the **Total** view, never Per 90: the engine computes rates from totals.
- If a row is **not shown** for a player, leave the cell **empty**. Never write 0 unless FotMob
  shows 0.
- Check the season tab says Super League 1 2026/2027 (not a cup).

## `teams.csv`

FotMob league team stats, `Average possession`, all 14 teams.

## `facts.csv` and `cards.csv` — the subject only (slgr.gr)

One row per Kalamata league match up to `last_match_date`. From the match sheet: starting XI
(`started`), `Time played` or substitution minutes (`minutes`), and `status`
(`played`, `unused_sub`, `suspended`, `injured`, `not_in_squad`, `unknown`). One row per card in
`cards.csv`; `reason` is `dissent_confirmed` only if seen on video, otherwise `foul`, `other` or
`unknown`.

## `history.csv` — the subject's past seasons (D6)

One row per season and competition from his FotMob page; leave fields empty where FotMob shows
nothing (no xA or xG exists for past seasons).

## Then

```bash
uv run c2e validate players/mendes-moreira --data-dir private/v1 --snapshot v1
uv run c2e run players/mendes-moreira --data-dir private/v1 --snapshot v1 --out private/v1/report
```

v1 is a private dry run: its report stays in `private/`.
