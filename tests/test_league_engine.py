"""Rule L end to end on small hand-built leagues: unavailable, insufficient, variants."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from c2e.config import Claim, LeaguePositionRule, PlayerConfig, Snapshot, load_metrics
from c2e.contracts import validate_league, validate_teams
from c2e.evidence import LeagueContext, Verdict, evaluate_league

METRICS = load_metrics(Path(__file__).parents[1] / "config" / "metrics.yaml")
SNAP = Snapshot(purpose="test", min_minutes=900, strict_min_minutes=1080)
PLAYER = PlayerConfig(
    id="t",
    name="Subject",
    team="T0",
    provider_id="S",
    attribution="test",
    is_synthetic=True,
    peer_positions=["LW"],
    min_peers=20,
    snapshots={"v": SNAP},
)


def league(
    n_peers: int = 20, subject_fouls: float = 60, minutes: int = 900, peer_minutes: int = 900
) -> pd.DataFrame:
    """Peers win 0..n-1 fouls in `peer_minutes`; the subject wins `subject_fouls`."""
    rows = [
        {
            "player_id": f"P{i}",
            "player_name": f"P{i}",
            "team": f"T{i % 4}",
            "position": "LW",
            "minutes": peer_minutes,
            "fouls_won": float(i),
            "tackles": float(i),
            "interceptions": 0.0,
        }
        for i in range(n_peers)
    ]
    rows.append(
        {
            "player_id": "S",
            "player_name": "Subject",
            "team": "T0",
            "position": "LW",
            "minutes": minutes,
            "fouls_won": subject_fouls,
            "tackles": 3.0,
            "interceptions": 0.0,
        }
    )
    rows.append(
        {
            "player_id": "X",
            "player_name": "Striker",
            "team": "T1",
            "position": "ST",
            "minutes": 2000,
            "fouls_won": 999.0,
            "tackles": 0.0,
            "interceptions": 0.0,
        }
    )
    df = pd.DataFrame(rows)
    df["source"], df["retrieved_at"] = "test", "2030-01-01"
    return validate_league(df)


def claim(metric: str, direction: str = "high", possession: bool = False) -> Claim:
    return Claim(
        id="C",
        question="Q",
        category="possession",
        report_text="r",
        statement="s",
        rule=LeaguePositionRule(
            type="league_position",
            metric=metric,
            direction=direction,
            possession_variant=possession,
        ),
        recruitment_relevance="high",
        data_confidence="high",
    )


def run(c: Claim, df: pd.DataFrame, teams: pd.DataFrame | None = None) -> Verdict:
    rule = c.rule
    assert isinstance(rule, LeaguePositionRule)
    return evaluate_league(c, rule, LeagueContext(df, teams, METRICS, PLAYER, SNAP)).verdict


def test_top_of_the_group_is_supported_and_strikers_are_not_peers() -> None:
    # Subject's 60 fouls beats all 20 peers; the striker with 999 is outside the peer positions.
    assert run(claim("fouls_won_p90"), league()) == Verdict.SUPPORTED


def test_middle_of_the_group() -> None:
    assert run(claim("fouls_won_p90"), league(subject_fouls=12)) == Verdict.PARTIALLY_SUPPORTED
    assert run(claim("fouls_won_p90"), league(subject_fouls=9)) == Verdict.NOT_SUPPORTED


def test_missing_column_is_unavailable_never_substituted() -> None:
    result = evaluate_league(
        claim("xa_p90"),
        claim("xa_p90").rule,  # type: ignore[arg-type]
        LeagueContext(league(), None, METRICS, PLAYER, SNAP),
    )
    assert result.verdict == Verdict.UNAVAILABLE
    assert "xa" in result.summary


def test_subject_without_any_stats_section_is_unavailable() -> None:
    df = league()
    df.loc[df["player_id"] == "S", ["fouls_won", "tackles", "interceptions"]] = np.nan
    assert run(claim("fouls_won_p90"), df) == Verdict.UNAVAILABLE


def test_absent_row_is_read_as_zero_and_the_method_1_0_reading_is_reported() -> None:
    df = league()
    df.loc[df["player_id"] == "S", "fouls_won"] = np.nan  # row omitted, other rows shown
    c = claim("fouls_won_p90", direction="low")
    result = evaluate_league(c, c.rule, LeagueContext(df, None, METRICS, PLAYER, SNAP))  # type: ignore[arg-type]
    assert result.analyses[0].data["value"] == 0.0
    assert "method 1.0 reading: not evaluable" in result.summary
    assert result.verdict == Verdict.SUPPORTED  # 0 is lower than 19 of the 20 peers (1 tied)


def test_subject_below_minimum_minutes_is_insufficient() -> None:
    assert run(claim("fouls_won_p90"), league(minutes=899)) == Verdict.INSUFFICIENT_DATA


def test_fewer_than_twenty_peers_is_insufficient_not_relaxed() -> None:
    assert run(claim("fouls_won_p90"), league(n_peers=19)) == Verdict.INSUFFICIENT_DATA


def test_peers_without_a_stats_section_drop_out_but_omitted_rows_count_as_zero() -> None:
    df = league(n_peers=21)
    df.loc[df["player_id"].isin(["P0", "P1"]), ["fouls_won", "tackles", "interceptions"]] = np.nan
    assert run(claim("fouls_won_p90"), df) == Verdict.INSUFFICIENT_DATA  # 19 peers left
    df = league(n_peers=21)
    df.loc[df["player_id"].isin(["P0", "P1"]), "fouls_won"] = np.nan  # omitted: read as 0
    c = claim("fouls_won_p90")
    result = evaluate_league(c, c.rule, LeagueContext(df, None, METRICS, PLAYER, SNAP))  # type: ignore[arg-type]
    assert result.analyses[0].data["n_peers"] == 21
    v10 = next(a for a in result.analyses if a.name == "main (method 1.0)")
    assert v10.verdict is None  # 19 peers under the method 1.0 reading


def test_strict_minutes_variant_can_lower_the_verdict() -> None:
    df = league(n_peers=40, subject_fouls=31)
    # The 20 best peers play 1080 minutes at the same rate (fouls × 1.2): among regular starters
    # only, the subject (3.1 per 90) beats 11 of 20 instead of 31 of 40.
    best = df["player_id"].isin([f"P{i}" for i in range(20, 40)])
    df.loc[best, "minutes"] = 1080
    df.loc[best, "fouls_won"] = df.loc[best, "fouls_won"] * 1.2
    result = evaluate_league(
        claim("fouls_won_p90"),
        claim("fouls_won_p90").rule,  # type: ignore[arg-type]
        LeagueContext(df, None, METRICS, PLAYER, SNAP),
    )
    main, strict = result.analyses[0], result.analyses[1]
    assert main.verdict == Verdict.SUPPORTED
    assert strict.verdict == Verdict.PARTIALLY_SUPPORTED
    assert result.verdict == Verdict.PARTIALLY_SUPPORTED


def test_possession_variant_lowers_a_weakness_claim_when_raw_and_adjusted_disagree() -> None:
    # Low tackle volume claim. Subject's team keeps the ball a lot (70%): adjusting scales his
    # volume up (× 50/30), so the weakness is no longer clear once possession is accounted for.
    df = league(n_peers=20)
    teams = validate_teams(
        pd.DataFrame(
            {
                "team": ["T0", "T1", "T2", "T3"],
                "possession_pct": [70.0, 40.0, 40.0, 40.0],
                "source": "test",
                "retrieved_at": "2030-01-01",
            }
        )
    )
    c = claim("tackles_interceptions_p90", direction="low", possession=True)
    result = evaluate_league(c, c.rule, LeagueContext(df, teams, METRICS, PLAYER, SNAP))  # type: ignore[arg-type]
    names = {a.name: a.verdict for a in result.analyses}
    assert names["main"] == Verdict.SUPPORTED
    assert names["possession_adjusted"] != Verdict.SUPPORTED
    assert result.verdict == names["possession_adjusted"]


def test_possession_variant_without_figures_is_not_evaluable_and_raw_stands() -> None:
    c = claim("tackles_interceptions_p90", direction="low", possession=True)
    result = evaluate_league(c, c.rule, LeagueContext(league(), None, METRICS, PLAYER, SNAP))  # type: ignore[arg-type]
    variant = next(a for a in result.analyses if a.name == "possession_adjusted")
    assert variant.verdict is None
    assert result.verdict == result.analyses[0].verdict


def test_subject_missing_from_snapshot_is_a_configuration_error() -> None:
    df = league()
    df = df[df["player_id"] != "S"]
    with pytest.raises(ValueError):
        run(claim("fouls_won_p90"), df)


def test_metric_variant_is_evaluated_where_available_and_never_replaces_the_main_metric() -> None:
    df = league(n_peers=20)
    c = Claim(
        id="C",
        question="Q",
        category="defensive",
        report_text="r",
        statement="s",
        rule=LeaguePositionRule(
            type="league_position",
            metric="tackles_p90",
            direction="low",
            variant_metrics=["tackles_interceptions_p90"],
        ),
        recruitment_relevance="high",
        data_confidence="high",
    )
    rule = c.rule
    assert isinstance(rule, LeaguePositionRule)
    df.loc[df["player_id"] == "S", "interceptions"] = np.nan  # row omitted for the subject
    res = evaluate_league(c, rule, LeagueContext(df, None, METRICS, PLAYER, SNAP))
    names = {a.name: a for a in res.analyses}
    assert names["metric:tackles_interceptions_p90"].verdict is not None  # read as 0
    old = names["metric:tackles_interceptions_p90 (method 1.0)"]
    assert old.verdict is None and "subject" in old.detail
    assert res.analyses[0].name == "main"  # the main metric decides first; variants only lower it
