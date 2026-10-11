# Coding quick reference

One page to keep open while watching a match. The full rules are in `TAGGING_PROTOCOL.md`; if
the two ever disagree, the protocol wins.

## Before kick-off

1. Add the match to `matches.csv` (`sample`: `pre_report`, `post_freeze` or `pilot`).
2. Watch the first 10 minutes, then write the first-half row of `segments.csv`:
   `wide_left` (left-most of a line of 3+), `front_two`, `am`, `other`. Add a row at half-time,
   after each substitution or visible change of shape, and an `off` row if he leaves the pitch.

## While watching — one row per event in `events.csv`

Zones are always from **his team's** point of view, attacking left → right.
Thirds `D` / `M` / `A`; lanes `LW` / `LHS` / `C` / `RHS` / `RW`.

| Event | When | Fill in |
|---|---|---|
| `chance_created` | His pass or cross → the receiver's **next action is a shot** | `phase`: `open_play`, `set_piece` (corner/free kick delivery or within 5 s of one), `unknown` |
| `fb_run` | Their right-back / right wing-back **passes him** heading to goal, in `LW`/`LHS`, `M`/`D`, after ≥ 5 s of their open-play possession | `third`, `lane`, `outcome`, `consequence` |
| `reception` | He receives a team-mate's pass in open play in `M` or `A` | `third`, `lane`, `outcome` (`to_feet` / `in_behind`), `between_lines` (`Y`/`N`) |
| `protest` | Complaint to an official for ~2 s or more, or he walks towards them | `outcome`: `none` / `yellow` |

### `fb_run` outcome — judge at the end moment

The run ends at the first of: the runner receives · possession changes or the ball goes out ·
the runner stops behind the ball for 3 s · 8 s have passed.

| Outcome | At the end moment |
|---|---|
| `tracked` | He is within ~5 m **and** level with or goal-side of the runner |
| `not_tracked` | Either condition fails, clearly visible |
| `ambiguous` | Off-screen, or the distance cannot be put clearly on one side of 5 m (six-yard box depth = 5.5 m) |
| `covered_by_teammate` | At the **start**, a team-mate was already within ~5 m and level or goal-side |

`consequence`: `cross`, `shot` or `goal` within 5 s of the same possession, otherwise `none`.

### Do not code

Set pieces and the first 5 s after a restart or a turnover · loose balls · receptions in `D` ·
anything from highlights · anything you only infer and did not see.

## Clock

`mm:ss` from the broadcast clock. Added time keeps counting: `46:30` in the first half is valid.

## After the match

Run `uv run c2e validate players/mendes-moreira --data-dir private/<snapshot>` and fix what it
reports. For the pilot, write down every situation the rules did not settle.
