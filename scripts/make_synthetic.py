"""Generate the fictional demo data in players/example/. Deterministic: same seed, same files.

Every player, team and match is invented. Nothing here comes from a real source.

    uv run python scripts/make_synthetic.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 2026
SOURCE = "synthetic"
RETRIEVED = "2030-12-21"
SUBJECT = "SYN-000"
TEAMS = [f"Synthetic FC {i:02d}" for i in range(1, 15)]
SUBJECT_TEAM = TEAMS[4]
PEER_POSITIONS = ["Attacking Midfielder", "Left Winger", "Right Winger"]
OTHER_POSITIONS = ["Striker", "Centre-Back", "Central Midfielder"]


def _league(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    n_peers, n_others = 60, 12
    for i in range(1, n_peers + n_others + 1):
        is_peer = i <= n_peers
        minutes = int(300 + 1050 * rng.beta(2.2, 1.1))
        r = {
            "chances_created": rng.normal(1.3, 0.45),
            "xa": rng.normal(0.15, 0.06),
            "npxg": rng.normal(0.22, 0.10),
            "touches_opp_box": rng.normal(3.0, 1.2),
            "dispossessed": rng.normal(1.6, 0.5),
            "fouls_won": rng.normal(1.5, 0.6),
            "tackles": rng.normal(1.0, 0.4),
            "interceptions": rng.normal(0.4, 0.2),
            "assists": rng.normal(0.12, 0.08),
            "goals": rng.normal(0.15, 0.1),
        }
        rows.append(
            _row(
                f"SYN-{i:03d}",
                f"Synthetic Player {i:03d}",
                TEAMS[int(rng.integers(0, len(TEAMS)))],
                str(rng.choice(PEER_POSITIONS if is_peer else OTHER_POSITIONS)),
                minutes,
                r,
                rng,
            )
        )
    subject_rates = {
        "chances_created": 2.4,
        "xa": 0.17,
        "npxg": 0.26,
        "touches_opp_box": 3.6,
        "dispossessed": 1.4,
        "fouls_won": 3.1,
        "tackles": 0.6,
        "interceptions": 0.2,
        "assists": 0.25,
        "goals": 0.05,
    }
    rows.append(
        _row(SUBJECT, "Example Player", SUBJECT_TEAM, "Left Winger", 1150, subject_rates, rng)
    )
    df = pd.DataFrame(rows)
    # This fictional provider does not publish touches: C05 must come out UNAVAILABLE.
    return df.drop(columns=["touches"])


def _row(
    pid: str,
    name: str,
    team: str,
    position: str,
    minutes: int,
    rates: dict[str, float],
    rng: np.random.Generator,
) -> dict[str, object]:
    out: dict[str, object] = {
        "player_id": pid,
        "player_name": name,
        "team": team,
        "position": position,
        "minutes": minutes,
    }
    for col, per90 in rates.items():
        expected = max(per90, 0.01) * minutes / 90
        if col in ("xa", "npxg"):
            out[col] = round(float(rng.gamma(4.0, expected / 4.0)), 2)
        else:
            out[col] = int(rng.poisson(expected))
    out["touches"] = int(rng.poisson(45 * minutes / 90))
    out["source"] = SOURCE
    out["retrieved_at"] = RETRIEVED
    out["url"] = ""
    return out


def _teams(rng: np.random.Generator) -> pd.DataFrame:
    possession = rng.uniform(38, 62, size=len(TEAMS)).round(1)
    df = pd.DataFrame(
        {"team": TEAMS, "possession_pct": possession, "source": SOURCE, "retrieved_at": RETRIEVED}
    )
    df.loc[df["team"] == SUBJECT_TEAM, "possession_pct"] = 42.0
    df.loc[df["team"] == TEAMS[-1], "possession_pct"] = np.nan  # one team without the figure
    return df


def _facts() -> tuple[pd.DataFrame, pd.DataFrame]:
    statuses = ["played"] * 13 + ["suspended", "played"]
    minutes = [90, 90, 90, 84, 90, 90, 72, 90, 90, 90, 61, 90, 90, 0, 90]
    facts = pd.DataFrame(
        {
            "match_id": [f"L{i:02d}" for i in range(1, 16)],
            "date": pd.date_range("2030-08-24", periods=15, freq="7D").strftime("%Y-%m-%d"),
            "opponent": [TEAMS[(i + 5) % len(TEAMS)] for i in range(15)],
            "status": statuses,
            "started": [s == "played" and m >= 60 for s, m in zip(statuses, minutes, strict=True)],
            "minutes": minutes,
            "source": SOURCE,
        }
    )
    cards = pd.DataFrame(
        {
            "match_id": ["L03", "L08", "L12"],
            "minute": [55, 71, 88],
            "card": ["yellow", "yellow", "yellow"],
            "reason": ["dissent_confirmed", "foul", "unknown"],
            "reason_source": ["own video", "own video", "no video available"],
        }
    )
    return facts, cards


def _history() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "season": ["2026/27", "2027/28", "2028/29", "2029/30"],
            "competition": [
                "Synthetic League",
                "Synthetic League",
                "Other Synthetic League",
                "Synthetic League 2",
            ],
            "team": ["Synthetic FC 09", "Synthetic FC 09", "Synthetic Club", SUBJECT_TEAM],
            "minutes": [1890, 2210, 1540, 2400],
            "chances_created": [31.0, 40.0, 22.0, None],
            "xa": [None, 3.1, 2.0, None],
            "npxg": [None, 2.4, 1.9, None],
            "source": SOURCE,
            "retrieved_at": RETRIEVED,
        }
    )


def _tagging(rng: np.random.Generator) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    match_ids = ["L01", "L02", "L03", "L05", "L06", "L07"]
    matches = pd.DataFrame(
        {
            "match_id": match_ids,
            "date": [
                "2030-08-24",
                "2030-08-31",
                "2030-09-07",
                "2030-09-21",
                "2030-09-28",
                "2030-10-05",
            ],
            "opponent": [TEAMS[(i + 5) % len(TEAMS)] for i in (0, 1, 2, 4, 5, 6)],
            "sample": ["pre_report"] * 3 + ["post_freeze"] * 3,
            "minutes_played": [90, 90, 90, 90, 90, 72],
            "protocol_version": "1.0",
            "video_source": "synthetic",
        }
    )
    roles = {
        "L01": "wide_left",
        "L02": "wide_left",
        "L03": "front_two",
        "L05": "wide_left",
        "L06": "wide_left",
        "L07": "wide_left",
    }
    seg_rows = []
    for mid in match_ids:
        role = roles[mid]
        shape = "back5" if role == "front_two" else "back4"
        seg_rows.append((mid, 1, 0.0, 50.0, role, shape))
        if mid == "L07":  # substituted at 72'
            seg_rows.append((mid, 2, 45.0, 72.0, role, shape))
            seg_rows.append((mid, 2, 72.0, 100.0, "off", shape))
        elif mid == "L02":  # switches to a front two after the break
            seg_rows.append((mid, 2, 45.0, 100.0, "front_two", "back5"))
        else:
            seg_rows.append((mid, 2, 45.0, 100.0, role, shape))
    segments = pd.DataFrame(
        seg_rows, columns=["match_id", "period", "from_min", "to_min", "his_role", "team_shape"]
    )

    events: list[dict[str, object]] = []

    def add(mid: str, period: int, minute: int, event: str, **kw: str) -> None:
        events.append(
            {
                "match_id": mid,
                "period": period,
                "clock": f"{minute}:{int(rng.integers(0, 60)):02d}",
                "event": event,
                "third": kw.get("third", ""),
                "lane": kw.get("lane", ""),
                "outcome": kw.get("outcome", ""),
                "phase": kw.get("phase", ""),
                "between_lines": kw.get("between_lines", ""),
                "consequence": kw.get("consequence", ""),
                "note": "",
            }
        )

    phases = {
        "L01": ["set_piece", "open_play", "open_play"],
        "L02": ["open_play", "set_piece"],
        "L03": ["open_play", "set_piece", "unknown"],
        "L05": ["open_play", "open_play"],
        "L06": ["set_piece", "open_play", "open_play"],
        "L07": ["open_play"],
    }
    runs = {
        "L01": ["not_tracked", "tracked", "not_tracked", "not_tracked", "ambiguous"],
        "L02": ["not_tracked", "tracked", "covered_by_teammate"],
        "L05": ["not_tracked", "not_tracked", "tracked", "not_tracked"],
        "L06": ["tracked", "not_tracked", "not_tracked", "ambiguous", "not_tracked"],
        "L07": ["not_tracked", "tracked", "not_tracked"],
    }
    protests = {"L01": 1, "L03": 2, "L05": 1, "L07": 1}
    for mid in match_ids:
        p1_max, p2_max = 44, 70 if mid == "L07" else 89
        for i, phase in enumerate(phases[mid]):
            add(
                mid,
                1 + i % 2,
                int(rng.integers(5, p1_max)) if i % 2 == 0 else int(rng.integers(46, p2_max)),
                "chance_created",
                phase=phase,
            )
        for outcome in runs.get(mid, []):
            consequence = (
                str(rng.choice(["none", "cross", "shot"])) if outcome == "not_tracked" else "none"
            )
            add(
                mid,
                1,
                int(rng.integers(2, p1_max)),
                "fb_run",
                third="D",
                lane=str(rng.choice(["LW", "LHS"])),
                outcome=outcome,
                consequence=consequence,
            )
        for _ in range(int(rng.integers(12, 19))):
            period = int(rng.integers(1, 3))
            minute = int(rng.integers(2, p1_max)) if period == 1 else int(rng.integers(46, p2_max))
            lane = str(rng.choice(["LW", "LHS", "C", "RHS"], p=[0.3, 0.4, 0.25, 0.05]))
            third = str(rng.choice(["M", "A"], p=[0.45, 0.55]))
            outcome = "in_behind" if rng.random() < 0.08 else "to_feet"
            add(
                mid,
                period,
                minute,
                "reception",
                third=third,
                lane=lane,
                outcome=outcome,
                between_lines="Y" if rng.random() < 0.35 else "N",
            )
        for _ in range(protests.get(mid, 0)):
            add(
                mid,
                2,
                int(rng.integers(46, p2_max)),
                "protest",
                outcome="yellow" if mid == "L03" else "none",
            )
    ev = pd.DataFrame(events)
    ev["_m"] = ev["clock"].str.split(":").str[0].astype(int)
    ev = ev.sort_values(["match_id", "period", "_m"]).drop(columns="_m")
    return matches, segments, ev


def main(root: Path) -> None:
    rng = np.random.default_rng(SEED)
    data, tagging = root / "data", root / "tagging"
    data.mkdir(parents=True, exist_ok=True)
    tagging.mkdir(parents=True, exist_ok=True)
    _league(rng).to_csv(data / "league_snapshot.csv", index=False)
    _teams(rng).to_csv(data / "teams.csv", index=False)
    facts, cards = _facts()
    facts.to_csv(data / "facts.csv", index=False)
    cards.to_csv(data / "cards.csv", index=False)
    _history().to_csv(data / "history.csv", index=False)
    matches, segments, events = _tagging(rng)
    matches.to_csv(tagging / "matches.csv", index=False)
    segments.to_csv(tagging / "segments.csv", index=False)
    events.to_csv(tagging / "events.csv", index=False)


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("players/example"))
