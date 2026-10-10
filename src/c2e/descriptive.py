"""Descriptive context (D1, D3, D5, D6 and card reasons). Nothing here produces a verdict."""

from __future__ import annotations

from collections import Counter

import pandas as pd

from c2e.contracts import records
from c2e.stats import rate_from_totals

UNAVAILABLE = "unavailable"


def _num(row: dict[str, object], col: str) -> float | None:
    value = row.get(col)
    if value is None or pd.isna(value):  # type: ignore[call-overload]
        return None
    return float(str(value))


def d1_assists_xa(league: pd.DataFrame, subject_id: str) -> str:
    """D1: assists alongside xA, worded neutrally."""
    row = next(r for r in records(league) if r["player_id"] == subject_id)
    assists, xa = _num(row, "assists"), _num(row, "xa")
    if assists is None:
        return "Assists: unavailable."
    if xa is None:
        return f"{assists:g} assists; xA unavailable."
    return f"{assists:g} assists from {xa:.2f} xA, season to date."


def d3_team_rank(
    league: pd.DataFrame, subject_id: str, min_minutes: int
) -> tuple[pd.DataFrame, str]:
    """D3: the subject's place within his own team in chances created per 90."""
    df = league.set_index("player_id")
    if "chances_created" not in df.columns or df["chances_created"].isna().all():
        return pd.DataFrame(), "Chances created: unavailable."
    team = df.loc[subject_id, "team"]
    mates = df[(df["team"] == team) & (df["minutes"] >= min_minutes)].copy()
    mates = mates.dropna(subset=["chances_created"])
    mates["chances_created_p90"] = [
        rate_from_totals([c], [m], 90)
        for c, m in zip(mates["chances_created"], mates["minutes"], strict=True)
    ]
    mates = mates.sort_values("chances_created_p90", ascending=False)
    table = mates[["player_name", "minutes", "chances_created", "chances_created_p90"]]
    if subject_id not in table.index:
        return table, f"Subject below {min_minutes} minutes; no team rank."
    value = table.loc[subject_id, "chances_created_p90"]
    higher = int((table["chances_created_p90"] > value).sum())
    return table, (
        f"{higher} team-mate(s) with ≥ {min_minutes} min create more chances per 90 "
        f"({len(table)} players compared)."
    )


def d5_availability(facts: pd.DataFrame) -> tuple[dict[str, int], pd.Series]:
    """D5: starts, minutes and absences in the team's league matches up to the snapshot."""
    played = facts[facts["status"] == "played"]
    summary = {
        "team_matches": len(facts),
        "starts": int(facts["started"].sum()),
        "appearances": len(played),
        "minutes": int(facts["minutes"].sum()),
        "possible_minutes": 90 * len(facts),
        "full_90": int((facts["minutes"] >= 90).sum()),
    }
    absences = facts.loc[facts["status"] != "played", "status"].value_counts()
    return summary, absences


def card_reasons(cards: pd.DataFrame) -> dict[tuple[str, str], int]:
    """Cards are facts; their reason is a classification, reported as such."""
    counts: Counter[tuple[str, str]] = Counter(
        (str(r["card"]), str(r["reason"])) for r in records(cards)
    )
    return dict(sorted(counts.items()))


def d6_history(history: pd.DataFrame) -> pd.DataFrame:
    """D6: one row per season and competition, never pooled; missing fields stay unavailable."""
    rows = []
    for row in records(history):
        out: dict[str, object] = {
            "season": row["season"],
            "competition": row["competition"],
            "team": row["team"],
            "minutes": row["minutes"],
        }
        for col in ("chances_created", "xa", "npxg"):
            raw = row.get(col)
            if raw is None or pd.isna(raw):
                out[f"{col}_p90"] = UNAVAILABLE
            else:
                value = rate_from_totals([float(raw)], [float(row["minutes"])], 90)
                out[f"{col}_p90"] = UNAVAILABLE if value is None else round(value, 2)
        rows.append(out)
    return pd.DataFrame(rows)
