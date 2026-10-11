"""Static figures for the evidence report. One look, one palette, verdicts never colour-only."""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from mplsoccer import Pitch

from c2e.config import ClaimsFile, LeaguePositionRule, MetricDef
from c2e.evidence import ClaimResult, Verdict
from c2e.metrics import compute_metric, missing_columns
from c2e.tagging import LANE_Y, THIRD_X

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#9a9893"
GRID = "#e5e4e0"
PEER = "#b5b3ad"
SUBJECT = "#2a78d6"
ACCENT = "#e34948"
RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95"]

VERDICT_STYLE: dict[Verdict, tuple[str, str]] = {
    Verdict.SUPPORTED: ("●", "#2a78d6"),
    Verdict.PARTIALLY_SUPPORTED: ("◐", "#86b6ef"),
    Verdict.INCONCLUSIVE: ("◌", "#9a9893"),
    Verdict.NOT_SUPPORTED: ("○", "#e34948"),
    Verdict.CONTRADICTED: ("✕", "#e34948"),
    Verdict.INSUFFICIENT_DATA: ("–", "#c3c2b7"),
    Verdict.UNAVAILABLE: ("–", "#c3c2b7"),
}

FOOTNOTE = "Verdicts apply pre-registered rules to small samples; they are not significance tests."

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.edgecolor": GRID,
        "axes.labelcolor": INK_2,
        "xtick.color": INK_2,
        "ytick.color": INK_2,
        "text.color": INK,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
    }
)


def _footer(fig: Figure, attribution: str, extra: str = "") -> None:
    note = f"{extra}  ·  {attribution}" if extra else attribution
    fig.text(0.01, 0.01, note, fontsize=7.5, color=MUTED, ha="left", va="bottom")


def claim_board(results: list[ClaimResult], title: str, attribution: str) -> Figure:
    """Every claim, its evidence type and verdict, with the number behind it."""
    rows = len(results)
    fig = plt.figure(figsize=(11, 1.2 + 0.62 * rows))
    ax = fig.add_axes((0.01, 0.06, 0.98, 0.86))
    ax.set_xlim(0, 1)
    ax.set_ylim(rows, -0.6)
    ax.axis("off")
    fig.text(0.01, 0.97, title, fontsize=14, weight="bold", va="top")
    for x, head in ((0.0, "Claim"), (0.47, "Evidence"), (0.6, "Verdict"), (0.79, "Basis")):
        ax.text(x, -0.35, head, fontsize=8.5, color=MUTED, weight="bold")
    for i, r in enumerate(results):
        if i:
            ax.axhline(i - 0.5, color=GRID, lw=0.8)
        statement = textwrap.fill(f"{r.claim.id}  {r.claim.statement}", 62)
        ax.text(0.0, i, statement, fontsize=8.8, va="center")
        ax.text(
            0.47, i, r.evidence_type.value.replace("_", " "), fontsize=8.3, color=INK_2, va="center"
        )
        symbol, colour = VERDICT_STYLE[r.verdict]
        ax.text(0.6, i, symbol, fontsize=13, color=colour, va="center")
        ax.text(0.625, i, r.verdict.value.replace("_", " ").lower(), fontsize=8.8, va="center")
        basis = textwrap.fill(r.summary.split(";")[0], 34)
        ax.text(0.79, i, basis, fontsize=7.8, color=INK_2, va="center")
    _footer(fig, attribution, FOOTNOTE)
    return fig


def _league_rows(
    results: list[ClaimResult],
    league: pd.DataFrame,
    metrics: dict[str, MetricDef],
    subject_id: str,
    positions: list[str],
    min_minutes: int,
) -> list[tuple[ClaimResult, MetricDef, pd.Series, float]]:
    rows = []
    for r in results:
        rule = r.claim.rule
        if not isinstance(rule, LeaguePositionRule) or r.verdict in (
            Verdict.UNAVAILABLE,
            Verdict.INSUFFICIENT_DATA,
        ):
            continue
        metric = metrics[rule.metric]
        if missing_columns(league, metric):
            continue
        values = compute_metric(league, metric).values
        mask = (
            league["position"].isin(positions)
            & (league["minutes"] >= min_minutes)
            & (league["player_id"] != subject_id)
        )
        peers = values.reindex(league.loc[mask, "player_id"]).dropna()
        rows.append((r, metric, peers, float(values[subject_id])))
    return rows


def peer_strips(
    results: list[ClaimResult],
    league: pd.DataFrame,
    metrics: dict[str, MetricDef],
    subject_id: str,
    subject_name: str,
    positions: list[str],
    min_minutes: int,
    attribution: str,
) -> Figure | None:
    """One strip per league claim: every peer as a dot, the subject highlighted."""
    rows = _league_rows(results, league, metrics, subject_id, positions, min_minutes)
    if not rows:
        return None
    fig, axes = plt.subplots(len(rows), 1, figsize=(9, 0.95 * len(rows) + 1.3), squeeze=False)
    rng = np.random.default_rng(0)
    for ax, (r, metric, peers, subject) in zip(axes[:, 0], rows, strict=True):
        jitter = rng.uniform(-0.18, 0.18, len(peers))
        ax.scatter(peers.values, jitter, s=22, color=PEER, edgecolor=SURFACE, lw=0.6, zorder=2)
        ax.axvline(peers.median(), color=INK_2, lw=1, ls=(0, (2, 2)), zorder=1)
        ax.scatter([subject], [0], s=90, color=SUBJECT, edgecolor=SURFACE, lw=2, zorder=3)
        ax.set_yticks([])
        ax.set_ylim(-0.5, 0.5)
        for side in ("left", "right", "top"):
            ax.spines[side].set_visible(False)
        ax.tick_params(axis="x", labelsize=8)
        rule = r.claim.rule
        assert isinstance(rule, LeaguePositionRule)
        arrow = "higher = claim" if rule.direction == "high" else "lower = claim"
        ax.set_title(
            f"{r.claim.id}  {metric.label}  ({arrow})", loc="left", fontsize=9.5, color=INK
        )
        main = r.analyses[0]
        word = "higher" if rule.direction == "high" else "lower"
        ax.text(
            1.0,
            1.02,
            f"{word} than {main.data['better_than']} of {main.data['n_peers']}",
            transform=ax.transAxes,
            ha="right",
            fontsize=8.5,
            color=INK_2,
        )
    fig.suptitle(
        f"{subject_name} (blue) among league peers (grey); dashed line = peer median",
        x=0.01,
        ha="left",
        fontsize=11,
        weight="bold",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))
    _footer(fig, attribution, f"Peers: {', '.join(positions)}; ≥ {min_minutes} minutes")
    return fig


def creation_vs_defence(
    league: pd.DataFrame,
    metrics: dict[str, MetricDef],
    subject_id: str,
    subject_name: str,
    positions: list[str],
    min_minutes: int,
    attribution: str,
) -> Figure | None:
    """xA per 90 against raw tackles + interceptions per 90: the trade-off in one picture."""
    x_def, y_def = metrics["tackles_interceptions_p90"], metrics["xa_p90"]
    if missing_columns(league, x_def) or missing_columns(league, y_def):
        return None
    xs, ys = compute_metric(league, x_def).values, compute_metric(league, y_def).values
    mask = (
        league["position"].isin(positions)
        & (league["minutes"] >= min_minutes)
        & (league["player_id"] != subject_id)
    )
    ids = [i for i in league.loc[mask, "player_id"] if i in xs.index and i in ys.index]
    if subject_id not in xs.index or subject_id not in ys.index or not ids:
        return None
    fig, ax = plt.subplots(figsize=(7.5, 6))
    ax.scatter(xs[ids], ys[ids], s=30, color=PEER, edgecolor=SURFACE, lw=0.6, label="peers")
    ax.axvline(float(xs[ids].median()), color=INK_2, lw=1, ls=(0, (2, 2)))
    ax.axhline(float(ys[ids].median()), color=INK_2, lw=1, ls=(0, (2, 2)))
    ax.scatter(
        [xs[subject_id]],
        [ys[subject_id]],
        s=110,
        color=SUBJECT,
        edgecolor=SURFACE,
        lw=2,
        zorder=3,
        label=subject_name,
    )
    ax.annotate(
        subject_name,
        (xs[subject_id], ys[subject_id]),
        xytext=(8, 8),
        textcoords="offset points",
        fontsize=9,
        color=INK,
    )
    ax.set_xlabel(f"{x_def.label} (raw)")
    ax.set_ylabel(y_def.label)
    ax.grid(color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for side in ("right", "top"):
        ax.spines[side].set_visible(False)
    ax.legend(frameon=False, loc="upper right", fontsize=8.5)
    ax.set_title(
        "Chance creation vs defensive volume (dashed lines: peer medians)",
        loc="left",
        fontsize=11,
        weight="bold",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    _footer(fig, attribution, f"Peers: ≥ {min_minutes} minutes; volume is not commitment")
    return fig


def pitch_map(
    zones: pd.DataFrame,
    events: pd.DataFrame,
    match_ids: list[str],
    attribution: str,
) -> Figure:
    """Left: where he receives. Right: the opponent full-back's runs past him, by outcome."""
    pitch = Pitch(
        pitch_type="statsbomb", pitch_color=SURFACE, line_color=MUTED, linewidth=1, line_zorder=2
    )
    fig: Figure
    fig, axes = pitch.draw(nrows=1, ncols=2, figsize=(13, 5))
    ax_rec, ax_runs = axes
    total = int(zones.to_numpy().sum())
    peak = max(int(zones.to_numpy().max()), 1)
    x_edges = {"M": (40, 80), "A": (80, 120)}
    y_edges = {"LW": (0, 18), "LHS": (18, 30), "C": (30, 50), "RHS": (50, 62), "RW": (62, 80)}
    for third, (x0, x1) in x_edges.items():
        for lane, (y0, y1) in y_edges.items():
            count = int(str(zones.at[third, lane])) if third in zones.index else 0
            shade = (
                RAMP[min(int(count / peak * (len(RAMP) - 1)), len(RAMP) - 1)] if count else SURFACE
            )
            ax_rec.add_patch(
                Rectangle(
                    (x0, y0),
                    x1 - x0,
                    y1 - y0,
                    facecolor=shade,
                    edgecolor=SURFACE,
                    lw=2,
                    zorder=1,
                    alpha=0.9,
                )
            )
            if count:
                ink = SURFACE if count / peak > 0.6 else INK
                ax_rec.text(
                    (x0 + x1) / 2,
                    (y0 + y1) / 2,
                    str(count),
                    ha="center",
                    va="center",
                    fontsize=10,
                    color=ink,
                    zorder=3,
                )
    ax_rec.set_title(
        f"Receptions by zone (n = {total}); attacking left → right", fontsize=10.5, loc="left"
    )

    runs = events[
        (events["event"] == "fb_run")
        & (events["his_role"] == "wide_left")
        & events["match_id"].isin(match_ids)
    ]
    styles = {
        "tracked": (PEER, "o"),
        "not_tracked": (ACCENT, "o"),
        "ambiguous": (MUTED, "x"),
        "covered_by_teammate": (INK_2, "s"),
    }
    rng = np.random.default_rng(1)
    for outcome, (colour, marker) in styles.items():
        sub = runs[runs["outcome"] == outcome]
        if sub.empty:
            continue
        xs = [THIRD_X[t] + rng.uniform(-14, 14) for t in sub["third"]]
        ys = [LANE_Y[lane] + rng.uniform(-6, 6) for lane in sub["lane"]]
        edge = None if marker == "x" else SURFACE
        ax_runs.scatter(
            xs,
            ys,
            s=60,
            color=colour,
            marker=marker,
            edgecolors=edge,
            lw=0.8,
            zorder=3,
            label=f"{outcome.replace('_', ' ')} ({len(sub)})",
        )
    ax_runs.legend(
        loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=4, fontsize=8.5, frameon=False
    )
    ax_runs.set_title(
        "Opponent full-back runs past him, as left-sided player (zone, jittered)",
        fontsize=10.5,
        loc="left",
    )
    _footer(fig, attribution, "Own video coding; positions are zone centres, not exact locations")
    return fig


RULE_TEXT = {
    "league_position": "League position vs peers",
    "video_proportion": "Own video coding",
    "match_majority": "Own video coding",
}


def _short(text: str, width: int) -> str:
    return text if len(text) <= width else text[: width - 1].rstrip() + "…"


def claim_map(claims: ClaimsFile, title: str, video_note: str | None = None) -> Figure:
    """Pre-registered claims as a table: what the report says → what is tested → how."""
    rows = claims.claims
    fig = plt.figure(figsize=(13, 1.9 + 0.66 * len(rows)))
    ax = fig.add_axes((0.01, 0.1, 0.98, 0.8))
    ax.set_xlim(0, 1)
    ax.set_ylim(len(rows), -0.7)
    ax.axis("off")
    fig.text(0.01, 0.97, title, fontsize=14, weight="bold", va="top")
    fig.text(
        0.01,
        0.925,
        "Each claim gets a test and a decision rule, fixed before the data is collected "
        f"(claims {claims.status}; method {claims.method_version})",
        fontsize=9.5,
        color=INK_2,
        va="top",
    )
    heads = ((0.0, "The scouting report says"), (0.36, "Tested statement"), (0.78, "Evidence"))
    for x, head in heads:
        ax.text(x, -0.45, head, fontsize=8.5, color=MUTED, weight="bold")
    for i, c in enumerate(rows):
        if i:
            ax.axhline(i - 0.5, color=GRID, lw=0.8)
        quote = textwrap.fill(f"{c.id}  “{_short(c.report_text, 95)}”", 52)
        ax.text(0.0, i, quote, fontsize=8.2, va="center", color=INK_2)
        ax.text(0.36, i, textwrap.fill(c.statement, 60), fontsize=8.4, va="center")
        evidence = RULE_TEXT[c.rule.type]
        unavailable = c.rule.type != "league_position" and video_note is not None
        if unavailable:
            evidence += " — unavailable"
        colour = MUTED if unavailable else INK
        ax.text(0.78, i, textwrap.fill(evidence, 24), fontsize=8.2, va="center", color=colour)
    notes = []
    if video_note:
        notes.append("Video claims unavailable: no legitimate full-match video of the league.")
    if claims.untested:
        topics = [u.report_text.split(".")[0].replace("…", "").strip() for u in claims.untested]
        notes.append(f"Not tested ({len(topics)}): " + "; ".join(topics) + ".")
    fig.text(
        0.01, 0.02, textwrap.fill("  ·  ".join(notes), 190), fontsize=7.8, color=MUTED, va="bottom"
    )
    return fig


def save(fig: Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
