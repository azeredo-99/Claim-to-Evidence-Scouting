"""The synthetic demo runs end to end, is reproducible, and matches the reviewed golden output."""

import filecmp
import importlib.util
from pathlib import Path

import pandas as pd

from c2e.pipeline import load_inputs, run
from c2e.report import claims_table, write_report

ROOT = Path(__file__).parents[1]
EXAMPLE = ROOT / "players" / "example"
GOLDEN = ROOT / "tests" / "golden" / "example_claims.csv"


def _example_run():  # type: ignore[no-untyped-def]
    inputs = load_inputs(EXAMPLE, EXAMPLE / "data", "v2", ROOT / "config" / "metrics.yaml")
    return run(inputs)


def test_synthetic_generator_is_deterministic_and_committed(tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location(
        "make_synthetic", ROOT / "scripts" / "make_synthetic.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main(tmp_path)
    for rel in (
        "data/league_snapshot.csv",
        "data/teams.csv",
        "data/facts.csv",
        "data/cards.csv",
        "data/history.csv",
        "tagging/matches.csv",
        "tagging/segments.csv",
        "tagging/events.csv",
    ):
        assert filecmp.cmp(tmp_path / rel, EXAMPLE / rel, shallow=False), rel


def test_example_verdicts_match_the_golden_file() -> None:
    table = claims_table(_example_run().results)[["id", "evidence_type", "verdict", "basis"]]
    golden = pd.read_csv(GOLDEN)
    pd.testing.assert_frame_equal(table.reset_index(drop=True), golden)


def test_every_verdict_state_is_reachable_by_the_demo_or_unit_tests() -> None:
    states = set(claims_table(_example_run().results)["verdict"])
    # The demo shows these; CONTRADICTED and INSUFFICIENT_DATA are covered in test_rules.py.
    assert {
        "SUPPORTED",
        "PARTIALLY_SUPPORTED",
        "NOT_SUPPORTED",
        "INCONCLUSIVE",
        "UNAVAILABLE",
    } <= states


def test_report_and_figures_are_written(tmp_path: Path) -> None:
    path = write_report(_example_run(), tmp_path)
    text = path.read_text(encoding="utf-8")
    assert "Synthetic demo" in text and "not significance tests" in text
    for fig in ("claim_board", "peer_strips", "creation_vs_defence", "pitch_map"):
        assert (tmp_path / "figures" / f"{fig}.png").stat().st_size > 10_000
    assert (tmp_path / "claims.csv").exists()


def test_real_player_configuration_is_valid_and_carries_no_data() -> None:
    player_dir = ROOT / "players" / "mendes-moreira"
    inputs = load_inputs(
        player_dir, ROOT / "private" / "does-not-exist", "v2", ROOT / "config" / "metrics.yaml"
    )
    assert inputs.claims.status == "frozen"
    assert inputs.player.provider_id == "947883"
    assert len(inputs.claims.claims) == 10
    assert inputs.league is None  # no third-party data ships with the repository


def test_only_synthetic_tables_are_committed() -> None:
    for csv in ROOT.glob("players/*/data/*.csv"):
        table = pd.read_csv(csv)
        assert "source" not in table.columns or set(table["source"]) == {"synthetic"}, csv


def test_coded_matches_must_belong_to_the_pre_registered_sample(tmp_path: Path) -> None:
    import shutil

    from c2e.contracts import DataContractError

    player = tmp_path / "p"
    shutil.copytree(EXAMPLE, player)
    matches = pd.read_csv(player / "tagging" / "matches.csv")
    matches.loc[matches["match_id"] == "L07", "opponent"] = "Synthetic FC 13"  # not in the plan
    matches.to_csv(player / "tagging" / "matches.csv", index=False)
    try:
        load_inputs(player, player / "data", "v2", ROOT / "config" / "metrics.yaml")
    except DataContractError as exc:
        assert "L07" in str(exc)
    else:
        raise AssertionError("a match outside the plan was accepted")
