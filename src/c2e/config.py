"""Typed configuration: metric definitions, player settings and pre-registered claims."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class MetricDef(_Strict):
    label: str
    numerator: list[str] = Field(min_length=1)
    denominator: str
    scale: float = Field(gt=0)
    unit: str
    source_label: str
    definition: str
    limitations: list[str] = []


class MetricsFile(_Strict):
    metrics: dict[str, MetricDef]


class LeaguePositionRule(_Strict):
    type: Literal["league_position"]
    metric: str
    direction: Literal["high", "low"]
    possession_variant: bool = False
    # Sensitivity analyses with a related metric, evaluated only where the source provides it.
    variant_metrics: list[str] = []


class VideoProportionRule(_Strict):
    type: Literal["video_proportion"]
    measure: Literal["open_play_share", "tracking_rate"]
    direction: Literal["greater", "less"]
    threshold: float = Field(default=0.5, gt=0, lt=1)


class MatchMajorityRule(_Strict):
    type: Literal["match_majority"]
    measure: Literal["protest_matches"]


Rule = Annotated[
    LeaguePositionRule | VideoProportionRule | MatchMajorityRule,
    Field(discriminator="type"),
]

Level = Literal["high", "medium", "low"]


class Claim(_Strict):
    id: str
    question: str
    category: Literal[
        "creation",
        "possession",
        "attacking",
        "defensive",
        "tactical",
        "discipline",
        "physical",
        "role",
    ]
    report_text: str
    statement: str
    rule: Rule
    recruitment_relevance: Level
    data_confidence: Level
    limitations: list[str] = []


class UntestedClaim(_Strict):
    report_text: str
    reason: str


class WithdrawnClaim(_Strict):
    id: str
    reason: str


class ClaimsFile(_Strict):
    player_id: str
    status: Literal["draft", "frozen"]
    method_version: str
    questions: dict[str, str]
    claims: list[Claim] = Field(min_length=1)
    untested: list[UntestedClaim] = []
    withdrawn: list[WithdrawnClaim] = []

    @model_validator(mode="after")
    def _unique_ids_and_known_questions(self) -> ClaimsFile:
        ids = [c.id for c in self.claims] + [w.id for w in self.withdrawn]
        duplicates = sorted({i for i in ids if ids.count(i) > 1})
        if duplicates:
            raise ValueError(f"duplicate claim ids: {duplicates}")
        unknown = sorted({c.question for c in self.claims} - set(self.questions))
        if unknown:
            raise ValueError(f"claims refer to unknown questions: {unknown}")
        return self


class Snapshot(_Strict):
    purpose: str
    last_match_date: dt.date | None = None
    snapshot_date: dt.date | None = None
    min_minutes: int = Field(gt=0)
    strict_min_minutes: int = Field(gt=0)

    @model_validator(mode="after")
    def _consistent(self) -> Snapshot:
        if self.strict_min_minutes <= self.min_minutes:
            raise ValueError("strict_min_minutes must be greater than min_minutes")
        if (
            self.last_match_date is not None
            and self.snapshot_date is not None
            and self.snapshot_date <= self.last_match_date
        ):
            raise ValueError("snapshot_date must be after last_match_date")
        return self


class PlannedMatch(_Strict):
    """A match in the pre-registered video sample, fixed before any of them is coded."""

    sample: Literal["pre_report", "post_freeze"]
    opponent: str
    date: dt.date | None = None


class DataPaths(_Strict):
    """Paths relative to the data directory given at run time."""

    league: str = "league_snapshot.csv"
    teams: str = "teams.csv"
    facts: str = "facts.csv"
    cards: str = "cards.csv"
    history: str = "history.csv"


class PlayerConfig(_Strict):
    id: str
    name: str
    team: str
    provider_id: str | None
    attribution: str
    is_synthetic: bool
    peer_positions: list[str] = Field(min_length=1)
    min_peers: int = Field(default=20, ge=2)
    video_n_min: int = Field(default=10, ge=1)
    video_z: float = Field(default=1.645, gt=0)
    match_min: int = Field(default=4, ge=2)
    snapshots: dict[str, Snapshot] = Field(min_length=1)
    video_sample: list[PlannedMatch] = []
    data: DataPaths = DataPaths()


def _read_yaml(path: Path) -> object:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_metrics(path: Path) -> dict[str, MetricDef]:
    return MetricsFile.model_validate(_read_yaml(path)).metrics


def load_player(path: Path) -> PlayerConfig:
    return PlayerConfig.model_validate(_read_yaml(path))


def load_claims(path: Path, metrics: dict[str, MetricDef]) -> ClaimsFile:
    claims = ClaimsFile.model_validate(_read_yaml(path))
    for claim in claims.claims:
        if isinstance(claim.rule, LeaguePositionRule):
            for name in [claim.rule.metric, *claim.rule.variant_metrics]:
                if name not in metrics:
                    raise ValueError(f"{claim.id}: unknown metric {name!r}")
    return claims
