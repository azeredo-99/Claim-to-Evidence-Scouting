"""Data contracts reject bad inputs; tagging counts follow the protocol."""

import pandas as pd
import pytest

from c2e.contracts import (
    DataContractError,
    clock_to_minutes,
    validate_cards,
    validate_facts,
    validate_league,
    validate_tagging,
    validate_teams,
)
from c2e.tagging import (
    open_play_counts,
    protest_matches,
    tracking_counts,
    with_roles,
    zone_centre,
)

PROV = {"source": "test", "retrieved_at": "2030-01-01"}


def matches(**kw: object) -> pd.DataFrame:
    base = {
        "match_id": ["m1", "m2"],
        "date": ["2030-01-01", "2030-01-08"],
        "opponent": ["A", "B"],
        "sample": ["pre_report", "post_freeze"],
        "minutes_played": [90, 90],
        "protocol_version": ["1.0", "1.0"],
        "video_source": ["x", "x"],
    }
    base.update(kw)
    return pd.DataFrame(base)


def segments(rows: list[tuple[str, int, float, float, str]] | None = None) -> pd.DataFrame:
    rows = rows or [
        ("m1", 1, 0, 50, "wide_left"),
        ("m1", 2, 45, 100, "front_two"),
        ("m2", 1, 0, 50, "wide_left"),
        ("m2", 2, 45, 100, "wide_left"),
    ]
    df = pd.DataFrame(rows, columns=["match_id", "period", "from_min", "to_min", "his_role"])
    df["team_shape"] = "back4"
    return df


def event(match_id: str, period: int, clock: str, ev: str, **kw: str) -> dict[str, object]:
    return {
        "match_id": match_id,
        "period": period,
        "clock": clock,
        "event": ev,
        "third": kw.get("third", ""),
        "lane": kw.get("lane", ""),
        "outcome": kw.get("outcome", ""),
        "phase": kw.get("phase", ""),
        "between_lines": kw.get("between_lines", ""),
        "consequence": kw.get("consequence", ""),
        "note": "",
    }


def run_(match_id: str, period: int, clock: str, outcome: str) -> dict[str, object]:
    return event(
        match_id, period, clock, "fb_run", third="D", lane="LW", outcome=outcome, consequence="none"
    )


class TestLeagueContracts:
    def test_negative_minutes_rejected(self) -> None:
        df = pd.DataFrame(
            {
                "player_id": ["a"],
                "player_name": ["A"],
                "team": ["T"],
                "position": ["LW"],
                "minutes": [-5],
                **{k: [v] for k, v in PROV.items()},
            }
        )
        with pytest.raises(DataContractError, match="minutes"):
            validate_league(df)

    def test_duplicate_player_ids_rejected(self) -> None:
        df = pd.DataFrame(
            {
                "player_id": ["a", "a"],
                "player_name": ["A", "B"],
                "team": ["T", "T"],
                "position": ["LW", "LW"],
                "minutes": [90, 90],
                **{k: [v, v] for k, v in PROV.items()},
            }
        )
        with pytest.raises(DataContractError):
            validate_league(df)

    def test_possession_must_be_strictly_between_0_and_100(self) -> None:
        with pytest.raises(DataContractError):
            validate_teams(
                pd.DataFrame(
                    {"team": ["T"], "possession_pct": [100.0], **{k: [v] for k, v in PROV.items()}}
                )
            )

    def test_facts_status_and_minutes_must_agree(self) -> None:
        df = pd.DataFrame(
            {
                "match_id": ["m1"],
                "date": ["2030-01-01"],
                "opponent": ["A"],
                "status": ["suspended"],
                "started": [False],
                "minutes": [30],
                "source": ["s"],
            }
        )
        with pytest.raises(DataContractError, match="suspended"):
            validate_facts(df)

    def test_cards_must_refer_to_known_matches(self) -> None:
        facts = validate_facts(
            pd.DataFrame(
                {
                    "match_id": ["m1"],
                    "date": ["2030-01-01"],
                    "opponent": ["A"],
                    "status": ["played"],
                    "started": [True],
                    "minutes": [90],
                    "source": ["s"],
                }
            )
        )
        cards = pd.DataFrame(
            {
                "match_id": ["m9"],
                "minute": [10],
                "card": ["yellow"],
                "reason": ["unknown"],
                "reason_source": ["none"],
            }
        )
        with pytest.raises(DataContractError, match="m9"):
            validate_cards(cards, facts)

    def test_card_reason_outside_taxonomy_rejected(self) -> None:
        facts = validate_facts(
            pd.DataFrame(
                {
                    "match_id": ["m1"],
                    "date": ["2030-01-01"],
                    "opponent": ["A"],
                    "status": ["played"],
                    "started": [True],
                    "minutes": [90],
                    "source": ["s"],
                }
            )
        )
        cards = pd.DataFrame(
            {
                "match_id": ["m1"],
                "minute": [10],
                "card": ["yellow"],
                "reason": ["dissent"],
                "reason_source": ["video"],
            }
        )
        with pytest.raises(DataContractError):
            validate_cards(cards, facts)


class TestTaggingContracts:
    def test_valid_tables_pass(self) -> None:
        ev = pd.DataFrame([run_("m1", 1, "12:30", "tracked")])
        validate_tagging(matches(), segments(), ev)

    @pytest.mark.parametrize(
        ("ev", "message"),
        [
            (
                event("m1", 1, "10:00", "fb_run", outcome="tracked", consequence="none"),
                "needs third and lane",
            ),
            (
                event(
                    "m1",
                    1,
                    "10:00",
                    "reception",
                    third="A",
                    lane="C",
                    outcome="tracked",
                    between_lines="N",
                ),
                "not valid for reception",
            ),
            (event("m1", 1, "10:00", "chance_created"), "needs a phase"),
            (event("m3", 1, "10:00", "protest", outcome="none"), "unknown matches"),
            (event("m1", 1, "61:00", "protest", outcome="none"), "beyond 60:00"),
            (event("m1", 2, "30:00", "protest", outcome="none"), "outside 45:00"),
        ],
    )
    def test_bad_events_rejected(self, ev: dict[str, object], message: str) -> None:
        with pytest.raises(DataContractError, match=message):
            validate_tagging(matches(), segments(), pd.DataFrame([ev]))

    def test_overlapping_segments_rejected(self) -> None:
        seg = segments([("m1", 1, 0, 50, "wide_left"), ("m1", 1, 40, 50, "front_two")])
        with pytest.raises(DataContractError, match="overlap"):
            validate_tagging(matches(), seg, pd.DataFrame([run_("m1", 1, "10:00", "tracked")]))

    def test_event_outside_any_segment_rejected(self) -> None:
        seg = segments([("m1", 1, 0, 30, "wide_left")])
        with pytest.raises(DataContractError, match="no segment"):
            validate_tagging(matches(), seg, pd.DataFrame([run_("m1", 1, "40:00", "tracked")]))

    def test_event_while_off_the_pitch_rejected(self) -> None:
        seg = segments([("m1", 2, 45, 70, "wide_left"), ("m1", 2, 70, 100, "off")])
        with pytest.raises(DataContractError, match="off the pitch"):
            validate_tagging(matches(), seg, pd.DataFrame([run_("m1", 2, "80:00", "tracked")]))


class TestTaggingCounts:
    def test_clock_and_added_time(self) -> None:
        assert clock_to_minutes("46:30") == pytest.approx(46.5)
        with pytest.raises(DataContractError):
            clock_to_minutes("4630")

    def test_role_follows_the_segment_including_first_half_added_time(self) -> None:
        seg = segments([("m1", 1, 0, 50, "wide_left"), ("m1", 2, 45, 100, "front_two")])
        ev = pd.DataFrame([run_("m1", 1, "46:30", "tracked"), run_("m1", 2, "46:30", "tracked")])
        _, s, e = validate_tagging(matches(), seg, ev)
        assert with_roles(e, s)["his_role"].tolist() == ["wide_left", "front_two"]

    def test_tracking_counts_main_and_ambiguity_variants(self) -> None:
        ev = pd.DataFrame(
            [
                run_("m1", 1, "05:00", "tracked"),
                run_("m1", 1, "10:00", "not_tracked"),
                run_("m1", 1, "15:00", "ambiguous"),
                run_("m1", 1, "20:00", "covered_by_teammate"),
                run_("m1", 2, "60:00", "not_tracked"),  # front_two: not part of C09
                run_("m2", 1, "05:00", "not_tracked"),
            ]
        )
        _, s, e = validate_tagging(matches(), segments(), ev)
        e = with_roles(e, s)
        main = tracking_counts(e, ["m1", "m2"], None)
        assert [(c.successes, c.n) for c in main] == [(1, 2), (0, 1)]
        as_t = tracking_counts(e, ["m1", "m2"], "tracked")
        assert [(c.successes, c.n) for c in as_t] == [(2, 3), (0, 1)]
        as_nt = tracking_counts(e, ["m1", "m2"], "not_tracked")
        assert [(c.successes, c.n) for c in as_nt] == [(1, 3), (0, 1)]

    def test_open_play_share_excludes_unknown_phase(self) -> None:
        ev = pd.DataFrame(
            [
                event("m1", 1, "05:00", "chance_created", phase=p)
                for p in ("open_play", "set_piece", "unknown", "open_play")
            ]
        )
        counts, unknown = open_play_counts(ev, ["m1", "m2"])
        assert [(c.successes, c.n) for c in counts] == [(2, 3), (0, 0)]
        assert unknown == 1

    def test_protest_matches_counts_matches_not_protests(self) -> None:
        ev = pd.DataFrame([event("m1", 2, "50:00", "protest", outcome="none")] * 3)
        assert protest_matches(ev, ["m1", "m2"]) == (1, 2)

    def test_zone_centres(self) -> None:
        assert zone_centre("A", "LHS") == (100.0, 24.0)
        assert zone_centre("D", "RW") == (20.0, 71.0)


def test_empty_tagging_templates_validate_and_give_insufficient_data(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from pathlib import Path

    from c2e.evidence import Verdict
    from c2e.pipeline import load_inputs, run

    root = Path(__file__).parents[1]
    result = run(
        load_inputs(
            root / "players" / "mendes-moreira", tmp_path, "v2", root / "config" / "metrics.yaml"
        )
    )
    verdicts = {r.claim.id: r.verdict for r in result.results}
    assert verdicts["C09"] == Verdict.INSUFFICIENT_DATA
    assert verdicts["C13"] == Verdict.INSUFFICIENT_DATA
    assert verdicts["C01"] == Verdict.UNAVAILABLE  # no league snapshot in the repository
