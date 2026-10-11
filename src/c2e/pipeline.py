"""Load, validate, evaluate. One function per stage so each can be tested on its own."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from c2e import contracts, descriptive, tagging
from c2e.config import (
    ClaimsFile,
    MetricDef,
    PlayerConfig,
    Snapshot,
    load_claims,
    load_metrics,
    load_player,
)
from c2e.evidence import ClaimResult, LeagueContext, VideoContext, evaluate


@dataclass(frozen=True)
class Inputs:
    player: PlayerConfig
    claims: ClaimsFile
    metrics: dict[str, MetricDef]
    snapshot_name: str
    snapshot: Snapshot
    league: pd.DataFrame | None
    teams: pd.DataFrame | None
    facts: pd.DataFrame | None
    cards: pd.DataFrame | None
    history: pd.DataFrame | None
    matches: pd.DataFrame | None
    segments: pd.DataFrame | None
    events: pd.DataFrame | None  # with `his_role`


@dataclass(frozen=True)
class RunResult:
    inputs: Inputs
    results: list[ClaimResult]
    d1: str | None
    d2: pd.DataFrame | None
    d3: tuple[pd.DataFrame, str] | None
    d4: tuple[pd.DataFrame, dict[str, int]] | None
    d5: tuple[dict[str, int], pd.Series] | None
    d6: pd.DataFrame | None
    cards: dict[tuple[str, str], int] | None


def _optional(path: Path) -> pd.DataFrame | None:
    return contracts.read_csv(path) if path.exists() else None


def check_video_sample(matches: pd.DataFrame, player: PlayerConfig) -> None:
    """Coded matches must belong to the pre-registered sample (no picking matches afterwards)."""
    if not player.video_sample:
        return
    problems = []
    for row in contracts.records(matches[matches["sample"] != "pilot"]):
        date = pd.Timestamp(row["date"]).date()
        ok = any(
            p.sample == row["sample"]
            and p.opponent == row["opponent"]
            and (p.date is None or p.date == date)
            for p in player.video_sample
        )
        if not ok:
            problems.append(f"{row['match_id']} ({row['sample']}, {row['opponent']}, {date})")
    if problems:
        raise contracts.DataContractError(
            "matches outside the pre-registered video sample:\n"
            + "\n".join(f"  - {p}" for p in problems)
        )


def load_inputs(player_dir: Path, data_dir: Path, snapshot_name: str, metrics_path: Path) -> Inputs:
    metrics = load_metrics(metrics_path)
    player = load_player(player_dir / "player.yaml")
    claims = load_claims(player_dir / "claims.yaml", metrics)
    if claims.player_id != player.id:
        raise ValueError(f"claims.yaml is for {claims.player_id!r}, not {player.id!r}")
    if snapshot_name not in player.snapshots:
        raise ValueError(f"unknown snapshot {snapshot_name!r}; known: {sorted(player.snapshots)}")

    paths = player.data
    league = _optional(data_dir / paths.league)
    league = contracts.validate_league(league) if league is not None else None
    teams = _optional(data_dir / paths.teams)
    teams = contracts.validate_teams(teams) if teams is not None else None
    facts = _optional(data_dir / paths.facts)
    facts = contracts.validate_facts(facts) if facts is not None else None
    cards = _optional(data_dir / paths.cards)
    if cards is not None:
        if facts is None:
            raise contracts.DataContractError("cards.csv needs facts.csv")
        cards = contracts.validate_cards(cards, facts)
    history = _optional(data_dir / paths.history)
    history = contracts.validate_history(history) if history is not None else None

    tag_dir = player_dir / "tagging"
    matches = segments = events = None
    if (tag_dir / "matches.csv").exists():
        matches, segments, raw_events = contracts.validate_tagging(
            contracts.read_csv(tag_dir / "matches.csv"),
            contracts.read_csv(tag_dir / "segments.csv"),
            contracts.read_csv(tag_dir / "events.csv"),
        )
        events = tagging.with_roles(raw_events, segments)
        check_video_sample(matches, player)

    return Inputs(
        player,
        claims,
        metrics,
        snapshot_name,
        player.snapshots[snapshot_name],
        league,
        teams,
        facts,
        cards,
        history,
        matches,
        segments,
        events,
    )


def run(inputs: Inputs) -> RunResult:
    p = inputs.player
    league_ctx = None
    if inputs.league is not None:
        league_ctx = LeagueContext(inputs.league, inputs.teams, inputs.metrics, p, inputs.snapshot)
    video_ctx = None
    match_ids: list[str] = []
    if inputs.matches is not None and inputs.events is not None:
        coded = tagging.coded_matches(inputs.matches)
        match_ids = coded["match_id"].tolist()
        samples = {
            s: coded.loc[coded["sample"] == s, "match_id"].tolist()
            for s in ("pre_report", "post_freeze")
            if (coded["sample"] == s).any()
        }
        video_ctx = VideoContext(inputs.events, match_ids, samples, p)

    results = evaluate(inputs.claims.claims, league_ctx, video_ctx, p.video_unavailable_reason)

    subject = p.provider_id
    d1 = None
    d3 = None
    if inputs.league is not None and subject and subject in set(inputs.league["player_id"]):
        d1 = descriptive.d1_assists_xa(inputs.league, subject)
        d3 = descriptive.d3_team_rank(inputs.league, subject, inputs.snapshot.min_minutes)
    d2 = d4 = None
    if inputs.events is not None and inputs.segments is not None:
        d2 = tagging.runs_by_role(inputs.events, inputs.segments, match_ids)
        d4 = (
            tagging.receptions_by_zone(inputs.events, match_ids),
            tagging.reception_shares(inputs.events, match_ids),
        )
    d5 = descriptive.d5_availability(inputs.facts) if inputs.facts is not None else None
    d6 = descriptive.d6_history(inputs.history) if inputs.history is not None else None
    cards = descriptive.card_reasons(inputs.cards) if inputs.cards is not None else None
    return RunResult(inputs, results, d1, d2, d3, d4, d5, d6, cards)
