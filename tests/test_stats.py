"""Hand-worked cases for every statistical helper, plus invariants checked with Hypothesis."""

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from c2e.stats import claim_aligned_position, possession_adjust, rate_from_totals, wilson_interval


class TestRateFromTotals:
    def test_three_events_in_270_minutes_is_one_per_90(self) -> None:
        assert rate_from_totals([3], [270], 90) == pytest.approx(1.0)

    def test_uses_totals_not_the_mean_of_match_rates(self) -> None:
        # 1 event in 10 min + 0 in 90 min: 90 × 1 / 100 = 0.90 (the mean of rates would be 4.50).
        assert rate_from_totals([1, 0], [10, 90], 90) == pytest.approx(0.90)

    def test_zero_minutes_is_excluded_not_divided(self) -> None:
        assert rate_from_totals([0], [0], 90) is None
        assert rate_from_totals([2, 1], [0, 0], 90) is None

    def test_per_100_touches(self) -> None:
        assert rate_from_totals([12], [600], 100) == pytest.approx(2.0)

    def test_rejects_negative_inputs_and_length_mismatch(self) -> None:
        with pytest.raises(ValueError):
            rate_from_totals([-1], [90], 90)
        with pytest.raises(ValueError):
            rate_from_totals([1, 2], [90], 90)


class TestPossessionAdjust:
    def test_low_possession_team_is_scaled_down(self) -> None:
        # 10 × 50 / (100 − 40) = 8.333…
        assert possession_adjust(10, 40) == pytest.approx(25 / 3)

    def test_fifty_percent_is_the_identity(self) -> None:
        assert possession_adjust(10, 50) == pytest.approx(10)

    def test_high_possession_team_is_scaled_up(self) -> None:
        assert possession_adjust(10, 60) == pytest.approx(12.5)

    @pytest.mark.parametrize("pos", [0, 100, -5, 120])
    def test_rejects_impossible_possession(self, pos: float) -> None:
        with pytest.raises(ValueError):
            possession_adjust(10, pos)


class TestWilson:
    def test_hand_worked_95_percent(self) -> None:
        # 6/22, z = 1.96: centre 0.3067, half-width 0.1750.
        lo, hi = wilson_interval(6, 22, 1.96)
        assert lo == pytest.approx(0.1316, abs=1e-3)
        assert hi == pytest.approx(0.4817, abs=1e-3)

    def test_hand_worked_one_sided_95(self) -> None:
        # 9/12, z = 1.645: lower bound ≈ 0.513, just above a 0.5 threshold.
        lo, _ = wilson_interval(9, 12, 1.645)
        assert lo == pytest.approx(0.513, abs=1e-3)

    def test_extremes_stay_inside_zero_one(self) -> None:
        assert wilson_interval(0, 10, 1.645)[0] == 0.0
        assert wilson_interval(10, 10, 1.645)[1] == 1.0

    @pytest.mark.parametrize(("x", "n"), [(1, 0), (-1, 5), (6, 5)])
    def test_rejects_impossible_counts(self, x: int, n: int) -> None:
        with pytest.raises(ValueError):
            wilson_interval(x, n, 1.645)

    @given(st.integers(1, 200).flatmap(lambda n: st.tuples(st.integers(0, n), st.just(n))))
    def test_interval_contains_the_estimate(self, xn: tuple[int, int]) -> None:
        x, n = xn
        lo, hi = wilson_interval(x, n, 1.645)
        assert 0 <= lo <= x / n <= hi <= 1


class TestClaimAlignedPosition:
    def test_subject_above_every_peer(self) -> None:
        pos = claim_aligned_position(4, [1, 2, 3], "high")
        assert (pos.better_than, pos.tied, pos.n_peers, pos.p_star) == (3, 0, 3, 1.0)

    def test_ties_count_against_the_claim(self) -> None:
        pos = claim_aligned_position(2, [1, 2, 2, 3], "high")
        assert (pos.better_than, pos.tied, pos.p_star) == (1, 2, 0.25)

    def test_low_direction_rewards_lower_values(self) -> None:
        pos = claim_aligned_position(1, [2, 3, 0.5], "low")
        assert (pos.better_than, pos.p_star) == (2, pytest.approx(2 / 3))

    def test_floating_point_noise_is_a_tie(self) -> None:
        pos = claim_aligned_position(0.1 + 0.2, [0.3], "high")
        assert (pos.better_than, pos.tied) == (0, 1)

    def test_needs_peers(self) -> None:
        with pytest.raises(ValueError):
            claim_aligned_position(1, [], "high")

    @given(st.floats(-1e6, 1e6), st.lists(st.floats(-1e6, 1e6), min_size=1, max_size=60))
    def test_directions_partition_the_peers(self, subject: float, peers: list[float]) -> None:
        high = claim_aligned_position(subject, peers, "high")
        low = claim_aligned_position(subject, peers, "low")
        assert 0 <= high.p_star <= 1
        assert high.tied == low.tied
        assert high.better_than + low.better_than + high.tied == len(peers)
        assert math.isclose(high.p_star, high.better_than / len(peers))
