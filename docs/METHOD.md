# Method

**Version:** 1.1 (2026-10-11). Version 1.0 was pre-registered at the tag `prereg-v1.0`, before any
player or peer data was collected; the only information seen beforehand was the list of field
labels (`docs/VERIFICATION_2026-10-11.md`). Version 1.1 changes one reading of the data, explained
in section 5 and in `DEVIATIONS.md`; the 1.0 verdict is still reported wherever it differs.

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-10-11 | Pre-registration (`prereg-v1.0`) |
| 1.1 | 2026-10-11 | An omitted statistic row is read as 0 for players whose stats section exists; the 1.0 reading (missing) stays as a sensitivity analysis |

## 1. Principle

Every important claim in the scouting report is tied to a metric or an observation protocol, a
reference population, and a decision rule written **before** the data is seen. The engine applies
the rules; it never weighs claims against each other and never produces a player score or a
recruitment decision. The final scouting conclusion is written by the scout.

## 2. Kinds of evidence

Each result carries an `evidence_type`, shown next to its verdict.

| `evidence_type` | What it is | What it can show | What it cannot show |
|---|---|---|---|
| `league_position` | Where the player's season value sits among league peers (point estimates) | Whether the season-to-date output is high or low *relative to a defined group* | That a difference is statistically significant, or that it reflects skill rather than role, team or sample |
| `video_estimate` | A proportion from the scout's own coding of full matches, with an approximate interval | Whether a behaviour happens more or less often than a stated threshold *in the coded sample* | Behaviour in matches not coded; anything the broadcast does not show |
| `video_count` | Matches in which a behaviour was observed at least once | Whether a behaviour recurs across matches | Its absence (the broadcast does not show everything) |
| `fact` | Official match facts (minutes, starts, cards) | What happened | Why it happened |
| `descriptive` | Context tables (D1–D6) | Context for the scout's reading | Any verdict |

Claims that need tactical context or data the project does not have are listed as **not tested**,
with the reason. They are not given a verdict.

## 3. Verdict states

| State | Used by | Meaning |
|---|---|---|
| `SUPPORTED` | L, V, M | L: the player is in the claim-aligned top quarter of peers. V: the interval and every leave-one-match-out estimate are on the claimed side of the threshold. M: the behaviour was seen in a majority of matches, robust to removing one |
| `PARTIALLY_SUPPORTED` | L | Claim-aligned above the median but not in the top quarter. A statement about degree, not about uncertainty |
| `NOT_SUPPORTED` | L, M | L: at or below the median in the claim's direction. M: seen in fewer than half of the matches. The data does not back the claim; it does not prove the opposite |
| `CONTRADICTED` | V | The interval and every leave-one-match-out estimate are on the opposite side of the threshold |
| `INCONCLUSIVE` | V, M | The data is compatible with both sides of the threshold, or sensitivity analyses disagree |
| `INSUFFICIENT_DATA` | all | Fewer minutes, peers, events or matches than the pre-registered minimum |
| `UNAVAILABLE` | all | The source does not provide the field |

No league verdict is a significance test. `CONTRADICTED` exists only where the evidence type can
actually point the other way (video proportions).

## 4. Data and provenance

- **League data:** FotMob season totals for Super League 1 (Greece), collected manually at a
  snapshot (see `DATA_SOURCES.md`).
  Every row carries `source`, `url` and `retrieved_at`. Raw snapshots are kept out of git.
- **Facts:** official match sheets (slgr.gr), cross-checked against another free source.
- **Video:** the scout's own coding under `TAGGING_PROTOCOL.md`.
- **Never mixed:** a metric's numerator and denominator come from the same source and snapshot;
  seasons and competitions are never pooled.

### Snapshots

| Snapshot | Rule | Minimum minutes | Strict-minutes variant | Purpose |
|---|---|---|---|---|
| `v1` | All league matches completed through round 10 | 450 | 675 | Private dry run |
| `v2` | All league matches completed before the winter break | 900 | 1080 | First publication |

`last_match_date` and `snapshot_date` are filled from the official calendar, with
`last_match_date < snapshot_date < first kick-off of the next round`. Postponed matches count only
if played on or before `last_match_date`. For `v1` this is 2026-11-08 (last round-10 match on
slgr.gr; Atromitos–AEK of round 7 had no date on 2026-10-11) with the snapshot on 2026-11-10. For `v2`
this is 2026-12-20 (last match of round 15) with the snapshot on 2026-12-22, before round 16 on
2027-01-09 (filled by the rule above after the pre-registration).

## 5. Metrics

All metrics are defined in `config/metrics.yaml` with definition, source label, unit, period,
transformation and limitations.

- **Per 90:** `90 × Σ events / Σ minutes`, from season totals. Never the mean of per-match rates.
  Zero minutes → the player is excluded from that metric, with the reason recorded.
- **Per 100 touches:** `100 × Σ events / Σ touches`. Zero touches → excluded.
- A missing value for a peer excludes that peer from that metric only; `N` is reported per metric.
- A metric missing from the source for every player → `UNAVAILABLE`. It is never replaced by a
  different metric.
- **Omitted rows (1.1).** FotMob omits a statistic row when its value is zero: in the rehearsal
  snapshot no explicit zero appeared for chances created, non-penalty xG, touches in the box,
  fouls won, tackles or interceptions, while players with up to 385 minutes lacked those rows.
  For a player whose stats section exists (at least one detailed statistic shown), an omitted row
  is therefore read as **0**. A player with no detailed statistic at all has no section and stays
  missing. Reading omitted rows as missing (the 1.0 rule) would drop exactly the lowest peers and
  favour every "low value" claim (C05, C07, C08). The 1.0 reading is kept as a sensitivity
  analysis: under Rule L the final verdict is the weakest of both, and the 1.0 verdict is printed
  when it differs.

## 6. Peer group

- **Inclusion:** the **first position FotMob lists** for the player on the squad page is one of
  `Attacking Midfielder`, `Left Winger`, `Right Winger`, `Left Midfielder`, `Right Midfielder`
  (labels confirmed on 2026-10-11), and Super League 1 minutes ≥ the snapshot minimum. Only the
  first listed position counts, so no player is counted twice; the subject's own label is reported.
  The subject is never part of his own reference group. Wide midfielders are included because in
  this league they play roles close to wingers, and the group would otherwise be small.
- **Minimum group size:** `N ≥ 20`. Rationale: with 20 peers, the top quarter holds 5 players, so
  the band does not hinge on one or two individuals. Below 20 → `INSUFFICIENT_DATA`.
- **Limitations of these thresholds:** 450 minutes is a floor for inclusion, not a reliability
  threshold; per-90 rates of peers near the floor are noisy and over-represented at the extremes.
  Attacking midfielders and wingers do not have identical roles, which matters most for defensive
  volume. The provider's primary position is a single label and may not reflect this season's role.
  Strikers are excluded, so a second striker playing in a front two has no exact peer group.

## 7. Rule L — league position

Let `σ = +1` if the claim says the value is high and `σ = −1` if it says low, and `v = σ × value`.

```
p* = #{peers with v strictly lower than the subject} / N
```

Ties count **against** the claim: a player only gets credit for peers he is strictly better than.
The number of tied peers is reported.

| p* | Verdict |
|---|---|
| ≥ 0.75 | `SUPPORTED` |
| > 0.50 and < 0.75 | `PARTIALLY_SUPPORTED` |
| ≤ 0.50 | `NOT_SUPPORTED` |

Presentation: value (2 decimals), event count, "better than k of N (t tied)". Never a percentile
with decimals. Each peer moves `p*` by `1/N` (5 points when `N = 20`), so a result close to a
boundary is reported as such.

### Sensitivity variants (pre-registered)

1. **Strict minutes:** the same rule with peers who played about 75–80% of the league minutes
   available at the snapshot (675 at round 10, 1080 before the winter break), i.e. regular
   starters. Evaluated only if the variant still has `N ≥ 20`; otherwise reported as
   "not evaluable". (A 1.5 × multiplier was rejected: at the winter break it would require
   every available minute.)
2. **Possession context (C08 only):** see section 8.

The final verdict is the **weakest** of the evaluable analyses (main + variants), in the order
`SUPPORTED > PARTIALLY_SUPPORTED > NOT_SUPPORTED`. All analyses are reported. If the main analysis
is not evaluable, the claim is `INSUFFICIENT_DATA` or `UNAVAILABLE`.

## 8. C08 — defensive volume and possession

- **Raw value — what it measures:** tackles per 90 minutes played, as FotMob reports them
  ("Tackles"; the provider does not say whether attempts or only won tackles count). It mixes the
  player's behaviour, his role, where he plays, and how often the opponent has the ball.
- **Why tackles and not tackles + interceptions:** at the field check FotMob did not show an
  "Interceptions" row for some attacking players, including the subject, while it did for a
  centre-back. An absent row is missing, not zero, so tackles + interceptions would leave the
  subject without a value. The absence may itself mean zero interceptions; dropping the component
  can only make a *low-volume* claim harder to support, so the choice is the conservative one.
  Tackles + interceptions remains a **sensitivity variant**, evaluated where available.
- **Possession-adjusted value — what it tries to measure:** volume per unit of defensive
  opportunity, using the opponent's share of possession as the proxy:
  `adjusted = raw × 50 / (100 − team possession %)`.
- **Assumptions it needs:** defensive opportunities grow in proportion to the opponent's
  possession; the team's season-average possession represents the minutes he played; the player's
  zone is exposed in the same proportion as the team.
- **Where it distorts:** forwards defend mainly in the press, which depends on how the opponent
  builds up, not on possession share; linear scaling exaggerates the correction for very
  low-possession teams (StatsBomb uses a sigmoid for this reason); game state (leading teams cede
  the ball); minutes that do not match the team's average.
- **Decision:** the **raw value is the primary metric**. The adjusted value is a **sensitivity
  variant**, not a better metric. Under Rule L the verdict is the weakest of the two, so the claim
  is only supported if it holds both with and without the possession correction. If team
  possession is unavailable, the variant is reported as not evaluable and the raw verdict stands.
  Team possession is FotMob's "Average possession" (team stats; all 14 teams listed).
- **What C08 can never show:** commitment, effort or positioning. Those are tested on video (C09).

## 9. Rule V — video proportions

- **Unit of analysis:** one opportunity as defined in `TAGGING_PROTOCOL.md` (one chance created
  for C04; one full-back run in a `wide_left` segment for C09).
- **Inclusion:** only events in matches coded under the frozen protocol; ambiguous events are
  excluded from the main analysis and used in the sensitivity variants.
- **Estimate:** `p̂ = x / n`, with a Wilson interval, `z = 1.645`:

  ```
  centre = (p̂ + z²/2n) / (1 + z²/n)
  half   = z · sqrt(p̂(1 − p̂)/n + z²/4n²) / (1 + z²/n)
  ```

  The claims are directional, so the bound on the claimed side is a one-sided 95% bound.
- **Leave-one-match-out (LOMO):** `p̂` is recomputed without each match that contributed at least
  one event. This is a heuristic for the clustering of events within matches, which the Wilson
  interval ignores.
- **Decision (threshold `t`, claimed direction):**
  - `SUPPORTED`: the claimed-side bound is beyond `t` and every LOMO estimate is strictly on the
    claimed side.
  - `CONTRADICTED`: the opposite-side bound is beyond `t` in the other direction and every LOMO
    estimate is strictly on the other side.
  - `INCONCLUSIVE`: otherwise.
  - `INSUFFICIENT_DATA`: `n < 10`. Rationale: below 10, one event moves the proportion by more
    than 10 percentage points.
- **Sensitivity (C09):** the main analysis excludes ambiguous runs; the variants count them all as
  tracked and all as not tracked. If the evaluable analyses agree, that is the verdict; if not, the
  verdict is `INCONCLUSIVE`.
- **Interpretation:** an estimate about the coded matches, from one coder. The interval assumes
  independent events, which is only approximately true.

## 10. Rule M — matches with a behaviour (C13)

- **Unit of analysis:** a coded match in which the player was on the pitch. `M` matches, `k` with
  at least one protest.
- `INSUFFICIENT_DATA` if `M < 4`.
- `SUPPORTED` if the majority survives removing one protest match: `(k − 1)/(M − 1) > 0.5`.
- `NOT_SUPPORTED` if `k/M < 0.5`.
- `INCONCLUSIVE` otherwise.
- **Why not Wilson:** with `M ≈ 6` an interval would always cross any threshold; a count with an
  explicit robustness condition is more honest.
- **Why no `CONTRADICTED`:** broadcasts do not show everything, so an unobserved protest is not
  evidence of no protest.
- **Cards** are facts; their reason (`dissent_confirmed`, `foul`, `other`, `unknown`) is a
  classification and is reported descriptively. A yellow card is never classified as dissent by
  default.

## 11. Descriptive analyses (no verdict)

- **D1:** "X assists from Y xA, season to date". No p-values; no words such as luck,
  over/underperformance or sustainable.
- **D2:** full-back runs and consequences by role and team shape; rates per 90 only for segments
  with ≥ 90 minutes.
- **D3:** the player's rank within his own team in chances created per 90.
- **D4:** receptions by zone, between the lines and in behind.
- **D5:** starts, minutes, full matches, absences and their reasons.
- **D6:** history by season and competition, one row each, never pooled.

## 12. What the engine does not do

It does not combine metrics, weight claims, rank players, compute similarity or produce a
recruitment decision. Passing software tests is not football validation.

## 13. Freezing and deviations

- `METHOD.md`, `config/metrics.yaml`, the player's `claims.yaml` and `player.yaml` (peer
  positions, snapshots, video sample) are frozen together at `prereg-v1.0`.
- `TAGGING_PROTOCOL.md` is frozen separately at `protocol-v1.0`, after the pilot and **before the
  first match of the video sample is coded**. The sample itself is already fixed in `player.yaml`,
  so the timing of the pilot cannot influence which matches are coded.
- Any later change creates a new version with date, reason and whether results had been seen.
  Results under the frozen version are always reported.
- Data problems found after a snapshot go to `DEVIATIONS.md`.
