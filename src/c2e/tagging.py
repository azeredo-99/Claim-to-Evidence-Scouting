"""Turn validated video-coding tables into the counts the claims and descriptive analyses need."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from c2e.contracts import LANES, THIRDS, clock_to_minutes, records

THIRD_X = {"D": 20.0, "M": 60.0, "A": 100.0}
LANE_Y = {"LW": 9.0, "LHS": 24.0, "C": 40.0, "RHS": 56.0, "RW": 71.0}


def zone_centre(third: str, lane: str) -> tuple[float, float]:
    """Centre of a zone in StatsBomb 120 × 80 coordinates (team attacking left to right)."""
    return THIRD_X[third], LANE_Y[lane]


@dataclass(frozen=True)
class MatchCount:
    match_id: str
    successes: int
    n: int


def coded_matches(matches: pd.DataFrame) -> pd.DataFrame:
    """Matches that count as evidence: not the pilot, and the player was on the pitch."""
    return matches[(matches["sample"] != "pilot") & (matches["minutes_played"] > 0)]


def with_roles(events: pd.DataFrame, segments: pd.DataFrame) -> pd.DataFrame:
    """Attach the player's role at the moment of each event (validation guarantees one segment)."""
    roles = []
    for row in records(events):
        minute = clock_to_minutes(str(row["clock"]))
        seg = segments[
            (segments["match_id"] == row["match_id"])
            & (segments["period"] == row["period"])
            & (segments["from_min"] <= minute)
            & (minute < segments["to_min"])
        ]
        roles.append(str(seg["his_role"].iloc[0]))
    out = events.copy()
    out["his_role"] = roles
    return out


def _per_match(
    events: pd.DataFrame, match_ids: list[str], success: pd.Series, include: pd.Series
) -> list[MatchCount]:
    counts = []
    for mid in match_ids:
        in_match = events["match_id"] == mid
        n = int((in_match & include).sum())
        x = int((in_match & include & success).sum())
        counts.append(MatchCount(mid, x, n))
    return counts


def open_play_counts(events: pd.DataFrame, match_ids: list[str]) -> tuple[list[MatchCount], int]:
    """C04: chances created from open play out of chances with a known phase; unknowns counted."""
    chances = events[events["event"] == "chance_created"]
    known = chances["phase"] != "unknown"
    counts = _per_match(chances, match_ids, chances["phase"] == "open_play", known)
    return counts, int((~known).sum())


def tracking_counts(
    events: pd.DataFrame, match_ids: list[str], ambiguous_as: str | None
) -> list[MatchCount]:
    """C09: tracked runs out of decided runs in `wide_left` segments.

    `ambiguous_as` is None (main analysis: ambiguous runs excluded), "tracked" or "not_tracked".
    Runs covered by a team-mate never enter the denominator.
    """
    runs = events[(events["event"] == "fb_run") & (events["his_role"] == "wide_left")]
    outcome = runs["outcome"]
    if ambiguous_as is not None:
        outcome = outcome.where(outcome != "ambiguous", ambiguous_as)
    include = outcome.isin(["tracked", "not_tracked"])
    return _per_match(runs, match_ids, outcome == "tracked", include)


def protest_matches(events: pd.DataFrame, match_ids: list[str]) -> tuple[int, int]:
    """C13: (matches with at least one protest, coded matches)."""
    protests = set(events.loc[events["event"] == "protest", "match_id"])
    return sum(1 for m in match_ids if m in protests), len(match_ids)


def role_minutes(segments: pd.DataFrame, match_ids: list[str]) -> pd.Series:
    seg = segments[segments["match_id"].isin(match_ids)]
    minutes = (seg["to_min"] - seg["from_min"]).groupby(seg["his_role"]).sum()
    return minutes.drop(labels=["off"], errors="ignore")


def runs_by_role(
    events: pd.DataFrame, segments: pd.DataFrame, match_ids: list[str]
) -> pd.DataFrame:
    """D2: full-back runs by role, outcome and consequence, with the minutes behind them."""
    runs = events[(events["event"] == "fb_run") & events["match_id"].isin(match_ids)]
    table = pd.crosstab(runs["his_role"], runs["outcome"])
    for col in ("tracked", "not_tracked", "covered_by_teammate", "ambiguous"):
        if col not in table.columns:
            table[col] = 0
    table = table[["tracked", "not_tracked", "covered_by_teammate", "ambiguous"]]
    led_to = runs[runs["outcome"] == "not_tracked"].groupby("his_role")["consequence"]
    table["untracked_to_cross_or_shot"] = led_to.apply(
        lambda s: int(s.isin(["cross", "shot", "goal"]).sum())
    )
    table = table.fillna(0).astype(int)
    minutes = role_minutes(segments, match_ids)
    table.insert(0, "minutes", minutes.reindex(table.index).fillna(0.0))
    return table


def receptions_by_zone(events: pd.DataFrame, match_ids: list[str]) -> pd.DataFrame:
    """D4: receptions counted by third and lane (rows: thirds A, M; columns: lanes)."""
    rec = events[(events["event"] == "reception") & events["match_id"].isin(match_ids)]
    grid = pd.crosstab(rec["third"], rec["lane"])
    return grid.reindex(index=[t for t in THIRDS if t != "D"], columns=list(LANES), fill_value=0)


def reception_shares(events: pd.DataFrame, match_ids: list[str]) -> dict[str, int]:
    rec = events[(events["event"] == "reception") & events["match_id"].isin(match_ids)]
    return {
        "receptions": len(rec),
        "between_lines": int((rec["between_lines"] == "Y").sum()),
        "in_behind": int((rec["outcome"] == "in_behind").sum()),
    }
