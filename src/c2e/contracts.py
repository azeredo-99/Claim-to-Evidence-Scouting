"""Data contracts for every input table. Validation fails loudly, listing every problem found."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
import pandera.pandas as pa
from pandera.errors import SchemaErrors

ROLES = ("wide_left", "front_two", "am", "other", "off")
EVENTS = ("chance_created", "fb_run", "reception", "protest")
THIRDS = ("D", "M", "A")
LANES = ("LW", "LHS", "C", "RHS", "RW")
OUTCOMES: dict[str, tuple[str, ...]] = {
    "chance_created": ("",),
    "fb_run": ("tracked", "not_tracked", "covered_by_teammate", "ambiguous"),
    "reception": ("to_feet", "in_behind"),
    "protest": ("none", "yellow"),
}
CLOCK = re.compile(r"^(\d{1,3}):([0-5]\d)$")

# Numeric snapshot columns that may be absent (→ UNAVAILABLE) or empty for a player.
LEAGUE_NUMERIC = (
    "assists",
    "goals",
    "chances_created",
    "xa",
    "npxg",
    "touches",
    "touches_opp_box",
    "dispossessed",
    "fouls_won",
    "tackles",
    "interceptions",
)


class DataContractError(ValueError):
    """Raised when an input table breaks its contract."""


def _non_negative() -> pa.Check:
    return pa.Check.ge(0)


def _provenance() -> dict[str, pa.Column]:
    return {
        "source": pa.Column(str, pa.Check.str_length(min_value=1)),
        "retrieved_at": pa.Column(pa.DateTime, coerce=True),
    }


LEAGUE = pa.DataFrameSchema(
    {
        "player_id": pa.Column(str, unique=True, coerce=True),
        "player_name": pa.Column(str),
        "team": pa.Column(str),
        "position": pa.Column(str),
        "minutes": pa.Column(int, _non_negative(), coerce=True),
        **{
            c: pa.Column(float, _non_negative(), nullable=True, required=False, coerce=True)
            for c in LEAGUE_NUMERIC
        },
        **_provenance(),
    },
    strict=False,
    coerce=True,
)

TEAMS = pa.DataFrameSchema(
    {
        "team": pa.Column(str, unique=True),
        "possession_pct": pa.Column(
            float,
            pa.Check.in_range(0, 100, include_min=False, include_max=False),
            nullable=True,
            coerce=True,
        ),
        **_provenance(),
    },
    strict=False,
    coerce=True,
)

FACTS = pa.DataFrameSchema(
    {
        "match_id": pa.Column(str, unique=True, coerce=True),
        "date": pa.Column(pa.DateTime, coerce=True),
        "opponent": pa.Column(str),
        "status": pa.Column(
            str,
            pa.Check.isin(
                ["played", "unused_sub", "suspended", "injured", "not_in_squad", "unknown"]
            ),
        ),
        "started": pa.Column(bool, coerce=True),
        "minutes": pa.Column(int, pa.Check.in_range(0, 130), coerce=True),
        "source": pa.Column(str),
    },
    strict=False,
    coerce=True,
)

CARDS = pa.DataFrameSchema(
    {
        "match_id": pa.Column(str, coerce=True),
        "minute": pa.Column(int, pa.Check.in_range(0, 130), coerce=True),
        "card": pa.Column(str, pa.Check.isin(["yellow", "second_yellow", "red"])),
        "reason": pa.Column(str, pa.Check.isin(["dissent_confirmed", "foul", "other", "unknown"])),
        "reason_source": pa.Column(str),
    },
    strict=False,
    coerce=True,
)

HISTORY = pa.DataFrameSchema(
    {
        "season": pa.Column(str),
        "competition": pa.Column(str),
        "team": pa.Column(str),
        "minutes": pa.Column(int, _non_negative(), coerce=True),
        **{
            c: pa.Column(float, _non_negative(), nullable=True, required=False, coerce=True)
            for c in ("chances_created", "xa", "npxg")
        },
        **_provenance(),
    },
    strict=False,
    coerce=True,
)

MATCHES = pa.DataFrameSchema(
    {
        "match_id": pa.Column(str, unique=True, coerce=True),
        "date": pa.Column(pa.DateTime, coerce=True),
        "opponent": pa.Column(str),
        "sample": pa.Column(str, pa.Check.isin(["pre_report", "post_freeze", "pilot"])),
        "minutes_played": pa.Column(int, pa.Check.in_range(0, 130), coerce=True),
        "protocol_version": pa.Column(str, coerce=True),
        "video_source": pa.Column(str),
    },
    strict=False,
    coerce=True,
)

SEGMENTS = pa.DataFrameSchema(
    {
        "match_id": pa.Column(str, coerce=True),
        "period": pa.Column(int, pa.Check.isin([1, 2]), coerce=True),
        "from_min": pa.Column(float, _non_negative(), coerce=True),
        "to_min": pa.Column(float, pa.Check.le(130), coerce=True),
        "his_role": pa.Column(str, pa.Check.isin(list(ROLES))),
        "team_shape": pa.Column(str, pa.Check.isin(["back4", "back3", "back5", "unknown"])),
    },
    strict=False,
    coerce=True,
)

EVENTS_SCHEMA = pa.DataFrameSchema(
    {
        "match_id": pa.Column(str, coerce=True),
        "period": pa.Column(int, pa.Check.isin([1, 2]), coerce=True),
        "clock": pa.Column(str, pa.Check.str_matches(CLOCK.pattern)),
        "event": pa.Column(str, pa.Check.isin(list(EVENTS))),
        "third": pa.Column(str, pa.Check.isin(["", *THIRDS])),
        "lane": pa.Column(str, pa.Check.isin(["", *LANES])),
        "outcome": pa.Column(str),
        "phase": pa.Column(str, pa.Check.isin(["", "open_play", "set_piece", "unknown"])),
        "between_lines": pa.Column(str, pa.Check.isin(["", "Y", "N"])),
        "consequence": pa.Column(str, pa.Check.isin(["", "none", "cross", "shot", "goal"])),
        "note": pa.Column(str),
    },
    strict=False,
    coerce=True,
)

_TEXT_COLUMNS = ("third", "lane", "outcome", "phase", "between_lines", "consequence", "note")


def records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Rows as plain dicts, for row-wise checks that span several columns."""
    return [{str(k): v for k, v in row.items()} for row in df.to_dict("records")]


def _validate(schema: pa.DataFrameSchema, df: pd.DataFrame, name: str) -> pd.DataFrame:
    try:
        return schema.validate(df, lazy=True)
    except SchemaErrors as exc:
        cases = exc.failure_cases[["column", "check", "failure_case"]].astype(str)
        lines = "\n".join(
            f"  - {r.column}: {r.check} ({r.failure_case})" for r in cases.itertuples()
        )
        raise DataContractError(f"{name} breaks its contract:\n{lines}") from None


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise DataContractError(f"missing input file: {path}")
    return pd.read_csv(path, dtype={"match_id": str, "player_id": str}, keep_default_na=True)


def validate_league(df: pd.DataFrame) -> pd.DataFrame:
    return _validate(LEAGUE, df, "league snapshot")


def validate_teams(df: pd.DataFrame) -> pd.DataFrame:
    return _validate(TEAMS, df, "teams")


def validate_facts(df: pd.DataFrame) -> pd.DataFrame:
    out = _validate(FACTS, df, "facts")
    problems = []
    for row in records(out):
        if row["status"] == "played" and row["minutes"] == 0:
            problems.append(f"{row['match_id']}: status 'played' with 0 minutes")
        if row["status"] != "played" and (row["minutes"] > 0 or row["started"]):
            problems.append(f"{row['match_id']}: status {row['status']!r} with minutes or a start")
    if problems:
        raise DataContractError("facts:\n" + "\n".join(f"  - {p}" for p in problems))
    return out


def validate_cards(df: pd.DataFrame, facts: pd.DataFrame) -> pd.DataFrame:
    out = _validate(CARDS, df, "cards")
    unknown = sorted(set(out["match_id"]) - set(facts["match_id"]))
    if unknown:
        raise DataContractError(f"cards refer to matches missing from facts: {unknown}")
    return out


def validate_history(df: pd.DataFrame) -> pd.DataFrame:
    out = _validate(HISTORY, df, "history")
    dup = out.duplicated(["season", "competition", "team"])
    if dup.any():
        raise DataContractError("history has duplicate season/competition/team rows")
    return out


def clock_to_minutes(clock: str) -> float:
    match = CLOCK.match(clock)
    if match is None:
        raise DataContractError(f"bad clock value: {clock!r}")
    return int(match.group(1)) + int(match.group(2)) / 60


def validate_tagging(
    matches: pd.DataFrame, segments: pd.DataFrame, events: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Validate the three tagging tables, including the rules that span columns and tables."""
    events = events.copy()
    for col in _TEXT_COLUMNS:
        if col in events.columns:
            events[col] = events[col].fillna("").astype(str)
    m = _validate(MATCHES, matches, "matches")
    s = _validate(SEGMENTS, segments, "segments")
    e = _validate(EVENTS_SCHEMA, events, "events")

    problems: list[str] = []
    known = set(m["match_id"])
    for name, table in (("segments", s), ("events", e)):
        orphans = sorted(set(table["match_id"]) - known)
        if orphans:
            problems.append(f"{name} refer to unknown matches: {orphans}")

    for seg in records(s):
        if seg["from_min"] >= seg["to_min"]:
            problems.append(f"segment {seg['match_id']} p{seg['period']}: from_min >= to_min")
    for (mid, period), grp in s.sort_values("from_min").groupby(["match_id", "period"]):
        starts, ends = grp["from_min"].tolist(), grp["to_min"].tolist()
        for prev_end, nxt_start in zip(ends, starts[1:], strict=False):
            if nxt_start < prev_end:
                problems.append(f"segments overlap in {mid} period {period}")

    for i, row in enumerate(records(e)):
        ev, period = str(row["event"]), int(row["period"])
        where = f"events row {i + 2} ({row['match_id']} {period} {row['clock']})"
        if row["outcome"] not in OUTCOMES[ev]:
            problems.append(f"{where}: outcome {row['outcome']!r} not valid for {ev}")
        if ev in ("fb_run", "reception") and (row["third"] == "" or row["lane"] == ""):
            problems.append(f"{where}: {ev} needs third and lane")
        if ev == "chance_created" and row["phase"] == "":
            problems.append(f"{where}: chance_created needs a phase")
        if ev == "reception" and row["between_lines"] == "":
            problems.append(f"{where}: reception needs between_lines")
        if ev == "fb_run" and row["consequence"] == "":
            problems.append(f"{where}: fb_run needs a consequence")
        if ev != "chance_created" and row["phase"] != "":
            problems.append(f"{where}: phase only applies to chance_created")
        minute = clock_to_minutes(str(row["clock"]))
        if period == 1 and minute >= 60:
            problems.append(f"{where}: period 1 clock beyond 60:00")
        if period == 2 and not 45 <= minute < 130:
            problems.append(f"{where}: period 2 clock outside 45:00-130:00")
        covering = s[
            (s["match_id"] == row["match_id"])
            & (s["period"] == period)
            & (s["from_min"] <= minute)
            & (minute < s["to_min"])
        ]
        if covering.empty:
            problems.append(f"{where}: no segment covers this moment")
        elif (covering["his_role"] == "off").any():
            problems.append(f"{where}: event while the player is off the pitch")

    if problems:
        raise DataContractError("tagging:\n" + "\n".join(f"  - {p}" for p in problems))
    return m, s, e
