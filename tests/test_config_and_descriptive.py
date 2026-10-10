"""Configuration guards and descriptive tables (which must never produce a verdict)."""

from pathlib import Path

import pandas as pd
import pytest
import yaml
from pydantic import ValidationError

from c2e.config import Snapshot, load_claims, load_metrics
from c2e.contracts import validate_facts, validate_history
from c2e.descriptive import d1_assists_xa, d5_availability, d6_history

ROOT = Path(__file__).parents[1]
METRICS = load_metrics(ROOT / "config" / "metrics.yaml")


def write_claims(tmp_path: Path, claims: list[dict[str, object]], **extra: object) -> Path:
    doc = {
        "player_id": "p",
        "status": "draft",
        "method_version": "x",
        "questions": {"Q1": "q"},
        "claims": claims,
        **extra,
    }
    path = tmp_path / "claims.yaml"
    path.write_text(yaml.safe_dump(doc))
    return path


def a_claim(cid: str = "C1", **rule: object) -> dict[str, object]:
    return {
        "id": cid,
        "question": "Q1",
        "category": "creation",
        "report_text": "r",
        "statement": "s",
        "rule": rule or {"type": "league_position", "metric": "xa_p90", "direction": "high"},
        "recruitment_relevance": "high",
        "data_confidence": "low",
    }


def test_every_metric_has_documentation() -> None:
    for name, m in METRICS.items():
        assert m.definition and m.unit and m.source_label and m.limitations, name


def test_duplicate_claim_ids_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="duplicate"):
        load_claims(write_claims(tmp_path, [a_claim(), a_claim()]), METRICS)


def test_unknown_metric_rejected(tmp_path: Path) -> None:
    path = write_claims(
        tmp_path, [a_claim(type="league_position", metric="rating", direction="high")]
    )
    with pytest.raises(ValueError, match="unknown metric"):
        load_claims(path, METRICS)


def test_unknown_question_rejected(tmp_path: Path) -> None:
    claim = a_claim()
    claim["question"] = "Q9"
    with pytest.raises(ValidationError, match="unknown questions"):
        load_claims(write_claims(tmp_path, [claim]), METRICS)


def test_unknown_rule_type_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        load_claims(write_claims(tmp_path, [a_claim(type="composite_score")]), METRICS)


def test_snapshot_dates_and_thresholds_must_be_consistent() -> None:
    with pytest.raises(ValidationError):
        Snapshot(purpose="x", min_minutes=900, strict_min_minutes=900)
    with pytest.raises(ValidationError):
        Snapshot(
            purpose="x",
            min_minutes=900,
            strict_min_minutes=1080,
            last_match_date="2030-12-20",
            snapshot_date="2030-12-20",
        )


def test_d1_is_worded_without_judgement() -> None:
    df = pd.DataFrame({"player_id": ["S"], "assists": [3.0], "xa": [1.234]})
    assert d1_assists_xa(df, "S") == "3 assists from 1.23 xA, season to date."
    df["xa"] = float("nan")
    assert d1_assists_xa(df, "S") == "3 assists; xA unavailable."


def test_d5_counts_facts() -> None:
    facts = validate_facts(
        pd.DataFrame(
            {
                "match_id": ["a", "b", "c"],
                "date": ["2030-01-01"] * 3,
                "opponent": ["x"] * 3,
                "status": ["played", "played", "suspended"],
                "started": [True, False, False],
                "minutes": [90, 25, 0],
                "source": ["s"] * 3,
            }
        )
    )
    summary, absences = d5_availability(facts)
    assert summary == {
        "team_matches": 3,
        "starts": 1,
        "appearances": 2,
        "minutes": 115,
        "possible_minutes": 270,
        "full_90": 1,
    }
    assert absences.to_dict() == {"suspended": 1}


def test_d6_keeps_seasons_apart_and_marks_missing_fields() -> None:
    hist = validate_history(
        pd.DataFrame(
            {
                "season": ["a", "b"],
                "competition": ["L1", "L2"],
                "team": ["T", "U"],
                "minutes": [900, 0],
                "chances_created": [10.0, 5.0],
                "xa": [None, 1.0],
                "source": ["s", "s"],
                "retrieved_at": ["2030-01-01"] * 2,
            }
        )
    )
    table = d6_history(hist)
    assert len(table) == 2  # never pooled
    assert table.loc[0, "chances_created_p90"] == 1.0
    assert table.loc[0, "xa_p90"] == "unavailable"
    assert table.loc[1, "chances_created_p90"] == "unavailable"  # zero minutes
    assert table.loc[0, "npxg_p90"] == "unavailable"  # column absent from the source
