"""Write the evidence report (Markdown), the claims table (CSV) and the figures."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from c2e import viz
from c2e.evidence import ClaimResult
from c2e.pipeline import RunResult

DISCLAIMER = (
    "Independent portfolio exercise. Not affiliated with any club and not a recruitment "
    "decision: the engine applies pre-registered rules; the scouting conclusion is written by "
    "the scout."
)


def claims_table(results: list[ClaimResult]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": r.claim.id,
                "question": r.claim.question,
                "statement": r.claim.statement,
                "evidence_type": r.evidence_type.value,
                "verdict": r.verdict.value,
                "basis": r.summary,
                "recruitment_relevance": r.claim.recruitment_relevance,
                "data_confidence": r.claim.data_confidence,
            }
            for r in results
        ]
    )


def _md_table(df: pd.DataFrame) -> str:
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.itertuples(index=False):
        cells = [str(v).replace("|", "/") for v in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _claim_detail(r: ClaimResult) -> list[str]:
    out = [
        f"### {r.claim.id} — {r.verdict.value.replace('_', ' ').lower()}",
        "",
        f'- **Report says:** "{r.claim.report_text}"',
        f"- **Tested statement:** {r.claim.statement}",
        f"- **Evidence type:** {r.evidence_type.value}",
        f"- **Rule:** `{r.claim.rule.model_dump_json()}`",
        f"- **Result:** {r.summary}",
    ]
    if r.analyses:
        out.append("- **Analyses (main + pre-registered sensitivity):**")
        out += [
            f"  - {a.name}: {a.verdict.value if a.verdict else 'not evaluable'} — {a.detail}"
            for a in r.analyses
        ]
    if r.subsets:
        out.append("- **By sample (descriptive):**")
        out += [f"  - {k}: {v}" for k, v in r.subsets.items()]
    if r.claim.limitations:
        out.append("- **Limitations:** " + " ".join(r.claim.limitations))
    out.append("")
    return out


def write_report(run: RunResult, out_dir: Path) -> Path:
    inp = run.inputs
    p, snap = inp.player, inp.snapshot
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = out_dir / "figures"
    figures: dict[str, str] = {}

    title = f"{p.name} — claims vs evidence ({inp.snapshot_name})"
    viz.save(viz.claim_board(run.results, title, p.attribution), fig_dir / "claim_board.png")
    figures["claim_board"] = "figures/claim_board.png"
    if inp.league is not None and p.provider_id:
        strips = viz.peer_strips(
            run.results,
            inp.league,
            inp.metrics,
            p.provider_id,
            p.name,
            p.peer_positions,
            snap.min_minutes,
            p.attribution,
        )
        if strips is not None:
            viz.save(strips, fig_dir / "peer_strips.png")
            figures["peer_strips"] = "figures/peer_strips.png"
        scatter = viz.creation_vs_defence(
            inp.league,
            inp.metrics,
            p.provider_id,
            p.name,
            p.peer_positions,
            snap.min_minutes,
            p.attribution,
        )
        if scatter is not None:
            viz.save(scatter, fig_dir / "creation_vs_defence.png")
            figures["creation_vs_defence"] = "figures/creation_vs_defence.png"
    if run.d4 is not None and inp.events is not None and inp.matches is not None:
        ids = inp.matches.loc[
            (inp.matches["sample"] != "pilot") & (inp.matches["minutes_played"] > 0), "match_id"
        ].tolist()
        viz.save(
            viz.pitch_map(run.d4[0], inp.events, ids, p.attribution), fig_dir / "pitch_map.png"
        )
        figures["pitch_map"] = "figures/pitch_map.png"

    table = claims_table(run.results)
    table.to_csv(out_dir / "claims.csv", index=False)

    md: list[str] = [f"# Evidence report — {p.name}", ""]
    if p.is_synthetic:
        md += ["> **Synthetic demo.** Every player, team, match and number here is invented.", ""]
    md += [
        f"> {DISCLAIMER}",
        "",
        f"- **Snapshot:** `{inp.snapshot_name}` — {snap.purpose}; last match "
        f"{snap.last_match_date or 'not set'}, collected {snap.snapshot_date or 'not set'}.",
        f"- **Claims file:** status `{inp.claims.status}`, method {inp.claims.method_version}.",
        f"- **Peers:** {', '.join(p.peer_positions)}; ≥ {snap.min_minutes} minutes "
        f"(strict variant ≥ {snap.strict_min_minutes}); at least {p.min_peers} required.",
        f"- **Data:** {p.attribution}",
        "",
        "## How to read this",
        "",
        "League verdicts describe where the player's season value sits among peers "
        "(`league_position`); they are **not significance tests**. Video verdicts come from the "
        "scout's own coding of a few matches (`video_estimate`, `video_count`). "
        "`INSUFFICIENT_DATA` and `UNAVAILABLE` are results, not failures.",
        "",
        "## Claims",
        "",
        f"![Claim board]({figures['claim_board']})",
        "",
        _md_table(table[["id", "question", "evidence_type", "verdict", "basis"]]),
        "",
    ]
    md += [line for r in run.results for line in _claim_detail(r)]
    for key, caption in (
        ("peer_strips", "League peers"),
        ("creation_vs_defence", "Creation vs defensive volume"),
        ("pitch_map", "Video coding"),
    ):
        if key in figures:
            md += [f"## {caption}", "", f"![{caption}]({figures[key]})", ""]

    md += ["## Descriptive context (no verdicts)", ""]
    if run.d1:
        md += [f"- **D1 — assists and xA:** {run.d1}"]
    if run.d3:
        md += [f"- **D3 — within his team:** {run.d3[1]}"]
    if run.d4:
        s = run.d4[1]
        md += [
            f"- **D4 — receptions:** {s['receptions']} coded; {s['between_lines']} between the "
            f"lines; {s['in_behind']} in behind (receptions, not runs)."
        ]
    if run.d5:
        f, absences = run.d5
        absent = ", ".join(f"{k}: {v}" for k, v in absences.items()) or "none"
        md += [
            f"- **D5 — availability:** {f['starts']} starts in {f['team_matches']} team "
            f"matches; {f['minutes']} of {f['possible_minutes']} possible minutes; "
            f"{f['full_90']} full matches; absences — {absent}."
        ]
    if run.cards is not None:
        cards = ", ".join(f"{card} ({reason}): {n}" for (card, reason), n in run.cards.items())
        md += [f"- **Cards (facts; reasons are classifications):** {cards}."]
    md += [""]
    if run.d2 is not None:
        md += [
            "**D2 — opponent full-back runs by his role**",
            "",
            _md_table(run.d2.reset_index()),
            "",
        ]
    if run.d6 is not None:
        md += [
            "**D6 — history, one row per season and competition (never pooled)**",
            "",
            _md_table(run.d6),
            "",
        ]

    if inp.claims.untested or inp.claims.withdrawn:
        md += ["## Not tested", ""]
        md += [f'- "{u.report_text}" — {u.reason}' for u in inp.claims.untested]
        md += [
            f"- {w.id} withdrawn before pre-registration — {w.reason}" for w in inp.claims.withdrawn
        ]
        md += [""]
    path = out_dir / "evidence-report.md"
    path.write_text("\n".join(md), encoding="utf-8")
    return path
