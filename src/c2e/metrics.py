"""League metrics computed from season totals in a snapshot."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from c2e.config import MetricDef
from c2e.stats import possession_adjust, rate_from_totals


@dataclass(frozen=True)
class MetricValues:
    """A metric for every player who has it, plus the raw totals behind each value."""

    values: pd.Series  # indexed by player_id; only players with a defined value
    events: pd.Series  # numerator totals, same index
    exposure: pd.Series  # denominator totals, same index
    excluded: dict[str, str]  # player_id -> reason


def missing_columns(df: pd.DataFrame, metric: MetricDef) -> list[str]:
    """Columns the metric needs that the source does not provide at all."""
    needed = [*metric.numerator, metric.denominator]
    return [c for c in needed if c not in df.columns or df[c].isna().all()]


def compute_metric(df: pd.DataFrame, metric: MetricDef) -> MetricValues:
    """`scale × Σ numerator / Σ denominator` for each player, from season totals."""
    if missing_columns(df, metric):
        raise KeyError(f"source lacks columns for {metric.label}: {missing_columns(df, metric)}")
    values: dict[str, float] = {}
    events: dict[str, float] = {}
    exposure: dict[str, float] = {}
    excluded: dict[str, str] = {}
    for row in df.itertuples(index=False):
        pid = str(row.player_id)
        nums = [getattr(row, c) for c in metric.numerator]
        den = getattr(row, metric.denominator)
        if any(pd.isna(x) for x in nums) or pd.isna(den):
            excluded[pid] = "value not reported"
            continue
        total = float(sum(nums))
        value = rate_from_totals([total], [float(den)], metric.scale)
        if value is None:
            excluded[pid] = f"zero {metric.denominator}"
            continue
        values[pid], events[pid], exposure[pid] = value, total, float(den)
    return MetricValues(
        values=pd.Series(values, dtype=float),
        events=pd.Series(events, dtype=float),
        exposure=pd.Series(exposure, dtype=float),
        excluded=excluded,
    )


def adjust_for_possession(
    values: pd.Series, team_of: pd.Series, possession: pd.Series
) -> tuple[pd.Series, list[str]]:
    """Possession-adjusted values; players whose team has no possession figure are dropped."""
    adjusted: dict[str, float] = {}
    dropped: list[str] = []
    for pid, value in values.items():
        team = team_of.get(pid)
        pos = possession.get(team) if team is not None else None
        if pos is None or pd.isna(pos):
            dropped.append(str(pid))
            continue
        adjusted[str(pid)] = possession_adjust(float(value), float(pos))
    return pd.Series(adjusted, dtype=float), dropped
