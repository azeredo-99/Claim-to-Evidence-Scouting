"""Decision rules: band boundaries, video proportions with LOMO, match majority."""

import pytest

from c2e.evidence import (
    Verdict,
    league_band,
    match_majority_verdict,
    proportion_analysis,
    weakest_league,
)
from c2e.tagging import MatchCount

V = Verdict


@pytest.mark.parametrize(
    ("p_star", "expected"),
    [
        (1.0, V.SUPPORTED),
        (0.75, V.SUPPORTED),
        (0.7499, V.PARTIALLY_SUPPORTED),
        (0.5001, V.PARTIALLY_SUPPORTED),
        (0.5, V.NOT_SUPPORTED),
        (0.0, V.NOT_SUPPORTED),
    ],
)
def test_league_band_boundaries(p_star: float, expected: Verdict) -> None:
    assert league_band(p_star) == expected


def test_weakest_league_verdict_wins() -> None:
    assert weakest_league([V.SUPPORTED, V.PARTIALLY_SUPPORTED]) == V.PARTIALLY_SUPPORTED
    assert weakest_league([V.SUPPORTED, V.NOT_SUPPORTED, V.SUPPORTED]) == V.NOT_SUPPORTED
    assert weakest_league([V.SUPPORTED]) == V.SUPPORTED


def _counts(*pairs: tuple[int, int]) -> list[MatchCount]:
    return [MatchCount(f"m{i}", x, n) for i, (x, n) in enumerate(pairs)]


def _verdict(counts: list[MatchCount], direction: str = "greater") -> Verdict | None:
    return proportion_analysis("main", counts, direction, 0.5, 10, 1.645).verdict


class TestVideoProportion:
    def test_below_minimum_events_is_insufficient(self) -> None:
        assert _verdict(_counts((8, 9))) == V.INSUFFICIENT_DATA

    def test_spread_evidence_is_supported(self) -> None:
        # 9/12, lower bound 0.513 > 0.5, and every leave-one-match-out estimate is 6/8.
        assert _verdict(_counts((3, 4), (3, 4), (3, 4))) == V.SUPPORTED

    def test_evidence_from_one_match_is_not_enough(self) -> None:
        # Same 9/12, but removing the first match leaves 0/3.
        assert _verdict(_counts((9, 9), (0, 3))) == V.INCONCLUSIVE

    def test_clear_opposite_is_contradicted(self) -> None:
        assert _verdict(_counts((1, 7), (1, 7))) == V.CONTRADICTED

    def test_exactly_on_the_threshold_is_inconclusive(self) -> None:
        assert _verdict(_counts((3, 6), (3, 6))) == V.INCONCLUSIVE

    def test_less_direction(self) -> None:
        # Tracking-rate style claim: tracked share below 0.5.
        assert _verdict(_counts((1, 6), (1, 6), (1, 5)), "less") == V.SUPPORTED
        assert _verdict(_counts((5, 6), (5, 6), (4, 5)), "less") == V.CONTRADICTED

    def test_matches_without_events_do_not_affect_lomo(self) -> None:
        assert _verdict(_counts((3, 4), (3, 4), (3, 4), (0, 0))) == V.SUPPORTED

    def test_reports_the_numbers_behind_the_verdict(self) -> None:
        a = proportion_analysis("main", _counts((3, 4), (3, 4), (3, 4)), "greater", 0.5, 10, 1.645)
        assert (a.data["x"], a.data["n"]) == (9, 12)
        assert a.data["lomo_min"] == pytest.approx(0.75)


@pytest.mark.parametrize(
    ("k", "m", "expected"),
    [
        (4, 6, V.SUPPORTED),
        (3, 6, V.INCONCLUSIVE),
        (2, 6, V.NOT_SUPPORTED),
        (3, 4, V.SUPPORTED),
        (2, 4, V.INCONCLUSIVE),
        (1, 4, V.NOT_SUPPORTED),
        (3, 3, V.INSUFFICIENT_DATA),
        (0, 0, V.INSUFFICIENT_DATA),
    ],
)
def test_match_majority(k: int, m: int, expected: Verdict) -> None:
    assert match_majority_verdict(k, m, 4) == expected
