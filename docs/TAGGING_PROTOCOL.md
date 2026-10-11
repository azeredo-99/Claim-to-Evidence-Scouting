# Video tagging protocol

**Version:** 1.0-rc2 (draft). Frozen at the tag `protocol-v1.0` after a 20-minute pilot on a match
of another team, and before the first match of the video sample is coded. Changes after the freeze
create a new version, and matches coded under different versions are reported separately.

## 1. Scope

Only what the claims and descriptive analyses need:

| Event | Feeds |
|---|---|
| `chance_created` | C04 (open play vs set piece) |
| `fb_run` | C09 (Tracking Rate), D2 |
| `reception` | D4 |
| `protest` | C13 |

Deliberately **not** coded: off-ball movement in general, build-up participation, pressing
intensity, weak-foot use, crossing defence. They cannot be observed reliably on a broadcast, or no
claim depends on them.

## 2. Sample

- Fixed on 2026-10-11 in `players/mendes-moreira/player.yaml`, before any of them was coded: the
  three matches already watched for the report (Aris, Volos, Panathinaikos) and the next three
  league matches (PAOK 12/10, OFI 18/10, Olympiacos 25/10). The pipeline rejects any coded match
  outside this list. If a match has no legitimate full video, it is reported as missing, not
  replaced.
- **Pilot:** 20 minutes of a match of another team, coding that team's left-sided attacking player
  with the same definitions (`sample=pilot`; its segments cover only the 20 minutes watched). The
  pilot is never used as evidence.
- Results for video claims are reported in total **and** split into `pre_report` and
  `post_freeze` matches.
- One match is re-coded at least 7 days later. Agreement and every disagreement are reported. This
  measures the coder's consistency, not agreement between coders.
- The match clock of every event is published, so anyone with access to the match can check each
  decision. No images or video are stored or published.

## 3. Files

`matches.csv` — one row per coded match.

| Column | Values |
|---|---|
| `match_id` | short id, unique |
| `date` | YYYY-MM-DD |
| `opponent` | text |
| `sample` | `pre_report` / `post_freeze` / `pilot` |
| `minutes_played` | integer, from the official match sheet |
| `protocol_version` | e.g. `1.0` |
| `video_source` | where it was watched (legitimate source) |

`segments.csv` — the player's role, coded **before** the events of that match.

| Column | Values |
|---|---|
| `match_id` | as above |
| `period` | 1 / 2 |
| `from_min`, `to_min` | match clock minutes, `from_min < to_min` |
| `his_role` | `wide_left` / `front_two` / `am` / `other` / `off` |
| `team_shape` | `back4` / `back3` / `back5` / `unknown` |

`events.csv` — one row per event.

| Column | Values |
|---|---|
| `match_id`, `period` | as above |
| `clock` | `mm:ss` of the broadcast clock; added time keeps counting (`46:30` in period 1 is valid). If the broadcast shows `45:00 +02:30`, code `47:30` |
| `event` | `chance_created` / `fb_run` / `reception` / `protest` |
| `third` | `D` / `M` / `A` (Kalamata's defensive, middle, attacking third) |
| `lane` | `LW` / `LHS` / `C` / `RHS` / `RW` |
| `outcome` | see each event |
| `phase` | `open_play` / `set_piece` / `unknown` (for `chance_created`) |
| `between_lines` | `Y` / `N` (for `reception`) |
| `consequence` | `none` / `cross` / `shot` / `goal` (for `fb_run`) |
| `note` | short free text |

## 4. Zones

Everything is coded from the point of view of the player's team attacking left to right
(StatsBomb 120 × 80: origin top-left, x = 120 is the opponent's goal line, y = 0 is the team's
left touchline).

- Thirds on x: `D` 0–40, `M` 40–80, `A` 80–120.
- Lanes on y: `LW` 0–18, `LHS` 18–30, `C` 30–50, `RHS` 50–62, `RW` 62–80 (penalty-box and six-yard
  box edges).

The code converts each zone to its centre for plotting. Zones are used instead of exact x, y,
which cannot be estimated reliably from a broadcast.

## 5. Roles (segments)

- `wide_left`: in the defensive organisation he occupies the left-most position of a line of
  three or more players (midfield or attack), whatever the back line.
- `front_two`: he is one of two forwards.
- `am`: central attacking midfielder behind the forwards.
- `other` / `off`: anything else / not on the pitch.

The role is set from the first 10 minutes of each half and after each substitution or visible
change of shape, before coding that period's events.

## 6. Event definitions

### `chance_created` (C04)

- **Counts:** his pass or cross after which the receiving team-mate's next action is a shot (any
  outcome). Includes assists.
- **Does not count:** a shot after a rebound, or after the receiver dribbles past an opponent.
- Any body part counts: a headed pass that sets up a shot is a `chance_created`.
- **Phase:** `set_piece` if the pass is the delivery of a corner or free kick, or is made within
  5 seconds of a corner or free kick taken by his team. Throw-ins are `open_play`. `unknown` if the
  restart is not visible; `unknown` is excluded from C04 and counted.

### `fb_run` (C09, D2)

Only coded in `wide_left` segments for C09; coded in every role for D2 exposure.

- **Runner:** the opponent who, at the start of the opponent's possession, is the right-most
  player of the opponent's back line (right-back in a back four, right wing-back in a back three or
  five). Fixed for that possession.
- **Start (all must hold):**
  1. The opponent has had the ball in open play for ≥ 5 seconds since winning it or since a
     restart (transitions and set pieces excluded).
  2. The runner moves forward and **passes him**: the runner's distance to his team's goal line
     becomes smaller than his.
  3. At that moment the runner is in `LW` or `LHS` and in `M` or `D`.
  4. No team-mate is within about 5 m of the runner and level with or goal-side of him. Otherwise
     code `covered_by_teammate` (decided at the start; it does not change if the team-mate leaves).
- **End (first of):** the runner receives the ball; possession changes or the ball goes out; the
  runner stops and stays behind the ball for ≥ 3 seconds; 8 seconds after the start.
- **Outcome at the end moment:**
  - `tracked`: he is within about 5 m of the runner **and** level with or goal-side of him (his
    distance to his own goal line is not more than about 1 m greater than the runner's).
  - `not_tracked`: either condition fails and the moment is clearly visible.
  - `ambiguous`: he or the runner is off-screen at the end moment, or the distance cannot be put
    clearly on one side of 5 m using pitch landmarks (six-yard box depth 5.5 m, penalty spot 11 m,
    centre circle radius 9.15 m).
  - `covered_by_teammate`: see start condition 4.
- **Consequence:** `cross`, `shot` or `goal` from the runner's action or the next action of the
  same possession within 5 seconds; otherwise `none`.
- **Repeated runs:** a new run starts only after the previous one ended and the start conditions
  hold again.
- **Back-line changes:** the runner stays the player identified at the start of the possession,
  even if the opponent's back line changes shape during it.
- **Still subjective:** distance estimation on a broadcast; "level with" when the camera is
  oblique; the exact end moment (±1 s); role assignment. Mitigations: the `ambiguous` category, the
  sensitivity analysis in `METHOD.md`, the re-coded match, the published clock.

### `reception` (D4)

- **Counts:** he receives a team-mate's pass in open play in `M` or `A`.
- **Does not count:** loose balls, receptions from set pieces or throw-ins, receptions in `D`.
- **Outcome:** `to_feet` or `in_behind` (received beyond the opponent's last defender).
- `between_lines`: `Y` if received behind the opponent's midfield line and in front of their back
  line.
- D4 measures **receptions**, not runs: a run that is never found by a pass is not recorded.

### `protest` (C13)

- **Counts:** a verbal or gestural complaint aimed at the referee or an assistant lasting about
  2 seconds or more, **or** in which he moves towards the official.
- **Does not count:** a raised arm asking for a decision during play.
- **Outcome:** `none` or `yellow` (card shown for it).

## 7. Out of scope

No claim about behaviour in matches that were not coded. No claim from highlights. Nothing from
the broadcast (images, clips, screenshots) goes into the repository.
