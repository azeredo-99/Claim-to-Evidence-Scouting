"""Small, hand-checkable statistical helpers. No hidden state, no library magic."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal


def rate_from_totals(
    events: Sequence[float], exposure: Sequence[float], scale: float
) -> float | None:
    """`scale × Σ events / Σ exposure`, e.g. per 90 minutes or per 100 touches.

    Never the mean of per-match rates. Returns None when the total exposure is zero, so that the
    caller excludes the player instead of dividing by zero.
    """
    if len(events) != len(exposure):
        raise ValueError("events and exposure must have the same length")
    if any(e < 0 for e in events) or any(x < 0 for x in exposure):
        raise ValueError("events and exposure must be non-negative")
    total = float(sum(exposure))
    if total == 0:
        return None
    return scale * float(sum(events)) / total


def possession_adjust(value: float, team_possession_pct: float) -> float:
    """Scale a defensive volume to a 50% possession baseline: `value × 50 / (100 − possession)`."""
    if not 0 < team_possession_pct < 100:
        raise ValueError("team possession must be strictly between 0 and 100")
    return value * 50.0 / (100.0 - team_possession_pct)


def wilson_interval(successes: int, n: int, z: float) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if n <= 0:
        raise ValueError("n must be positive")
    if not 0 <= successes <= n:
        raise ValueError("successes must be between 0 and n")
    p = successes / n
    z2 = z * z
    denom = 1 + z2 / n
    centre = (p + z2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denom
    # The exact bounds at the extremes are 0 and 1; floating point would give 1e-16 off.
    lo = 0.0 if successes == 0 else max(0.0, centre - half)
    hi = 1.0 if successes == n else min(1.0, centre + half)
    return lo, hi


@dataclass(frozen=True)
class Position:
    """Where a value sits among peers, from the claim's point of view."""

    p_star: float  # share of peers the subject is strictly better than
    better_than: int
    tied: int
    n_peers: int


def claim_aligned_position(
    subject: float, peers: Sequence[float], direction: Literal["high", "low"]
) -> Position:
    """Share of peers strictly worse than the subject for the claim; ties count against it."""
    if not peers:
        raise ValueError("at least one peer is required")
    sign = 1.0 if direction == "high" else -1.0
    v = sign * subject
    better = tied = 0
    for peer in peers:
        w = sign * peer
        # Rates computed from different totals can differ in the last bits; treat those as ties.
        if math.isclose(w, v, rel_tol=1e-9, abs_tol=1e-12):
            tied += 1
        elif w < v:
            better += 1
    return Position(p_star=better / len(peers), better_than=better, tied=tied, n_peers=len(peers))
