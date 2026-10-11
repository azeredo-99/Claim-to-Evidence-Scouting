"""The claim-to-evidence engine: apply each pre-registered rule and keep every analysis visible."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum

import pandas as pd

from c2e.config import (
    Claim,
    LeaguePositionRule,
    MatchMajorityRule,
    MetricDef,
    PlayerConfig,
    Snapshot,
    VideoProportionRule,
)
from c2e.metrics import adjust_for_possession, compute_metric, missing_columns
from c2e.stats import claim_aligned_position, wilson_interval
from c2e.tagging import MatchCount, open_play_counts, protest_matches, tracking_counts


class Verdict(StrEnum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNAVAILABLE = "UNAVAILABLE"


class EvidenceType(StrEnum):
    LEAGUE_POSITION = "league_position"
    VIDEO_ESTIMATE = "video_estimate"
    VIDEO_COUNT = "video_count"


# Rule L verdicts from strongest to weakest support.
_L_ORDER = (Verdict.SUPPORTED, Verdict.PARTIALLY_SUPPORTED, Verdict.NOT_SUPPORTED)

Datum = float | int | str | None


@dataclass(frozen=True)
class Analysis:
    """One pre-registered analysis (main or sensitivity). `verdict` None means not evaluable."""

    name: str
    verdict: Verdict | None
    detail: str
    data: dict[str, Datum] = field(default_factory=dict)


@dataclass(frozen=True)
class ClaimResult:
    claim: Claim
    verdict: Verdict
    evidence_type: EvidenceType
    summary: str
    analyses: tuple[Analysis, ...] = ()
    subsets: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class LeagueContext:
    league: pd.DataFrame
    teams: pd.DataFrame | None
    metrics: dict[str, MetricDef]
    player: PlayerConfig
    snapshot: Snapshot


@dataclass(frozen=True)
class VideoContext:
    events: pd.DataFrame  # validated, with `his_role`
    match_ids: list[str]  # coded matches that count as evidence
    samples: dict[str, list[str]]  # e.g. {"pre_report": [...], "post_freeze": [...]}
    player: PlayerConfig


# --------------------------------------------------------------------------- Rule L


def league_band(p_star: float) -> Verdict:
    if p_star >= 0.75:
        return Verdict.SUPPORTED
    if p_star > 0.5:
        return Verdict.PARTIALLY_SUPPORTED
    return Verdict.NOT_SUPPORTED


def weakest_league(verdicts: Sequence[Verdict]) -> Verdict:
    return max(verdicts, key=_L_ORDER.index)


def _band_text(p_star: float) -> str:
    if p_star >= 0.75:
        return "top quarter"
    if p_star > 0.5:
        return "above the median, below the top quarter"
    return "at or below the median"


def _position_analysis(
    name: str,
    subject_id: str,
    values: pd.Series,
    eligible: pd.Index,
    rule: LeaguePositionRule,
    min_peers: int,
) -> Analysis:
    peers = values.reindex(eligible).dropna()
    if len(peers) < min_peers:
        return Analysis(
            name,
            None,
            f"not evaluable: {len(peers)} peers (< {min_peers})",
            {"n_peers": len(peers)},
        )
    subject = float(values[subject_id])
    pos = claim_aligned_position(subject, peers.tolist(), rule.direction)
    verdict = league_band(pos.p_star)
    word = "higher" if rule.direction == "high" else "lower"
    detail = (
        f"{word} than {pos.better_than} of {pos.n_peers} peers ({pos.tied} tied): "
        f"{_band_text(pos.p_star)}"
    )
    return Analysis(
        name,
        verdict,
        detail,
        {
            "value": subject,
            "p_star": pos.p_star,
            "better_than": pos.better_than,
            "tied": pos.tied,
            "n_peers": pos.n_peers,
            "peer_median": float(peers.median()),
            "peer_q25": float(peers.quantile(0.25)),
            "peer_q75": float(peers.quantile(0.75)),
        },
    )


def _eligible(ctx: LeagueContext, min_minutes: int, subject_id: str) -> pd.Index:
    df = ctx.league
    mask = (
        df["position"].isin(ctx.player.peer_positions)
        & (df["minutes"] >= min_minutes)
        & (df["player_id"] != subject_id)
    )
    return pd.Index(df.loc[mask, "player_id"].astype(str))


def evaluate_league(claim: Claim, rule: LeaguePositionRule, ctx: LeagueContext) -> ClaimResult:
    etype = EvidenceType.LEAGUE_POSITION
    metric = ctx.metrics[rule.metric]
    absent = missing_columns(ctx.league, metric)
    if absent:
        return ClaimResult(
            claim, Verdict.UNAVAILABLE, etype, f"source does not provide: {', '.join(absent)}"
        )

    subject_id = ctx.player.provider_id
    rows = ctx.league[ctx.league["player_id"] == subject_id]
    if subject_id is None or rows.empty:
        raise ValueError(f"subject {subject_id!r} is not in the league snapshot")
    minutes = int(rows["minutes"].iloc[0])
    if minutes < ctx.snapshot.min_minutes:
        return ClaimResult(
            claim,
            Verdict.INSUFFICIENT_DATA,
            etype,
            f"{minutes} minutes (< {ctx.snapshot.min_minutes})",
        )

    mv = compute_metric(ctx.league, metric)
    if subject_id not in mv.values.index:
        reason = mv.excluded.get(subject_id, "no value")
        verdict = (
            Verdict.UNAVAILABLE if reason == "value not reported" else Verdict.INSUFFICIENT_DATA
        )
        return ClaimResult(claim, verdict, etype, f"subject: {reason}")

    analyses = [
        _position_analysis(
            "main",
            subject_id,
            mv.values,
            _eligible(ctx, ctx.snapshot.min_minutes, subject_id),
            rule,
            ctx.player.min_peers,
        ),
        _position_analysis(
            "strict_minutes",
            subject_id,
            mv.values,
            _eligible(ctx, ctx.snapshot.strict_min_minutes, subject_id),
            rule,
            ctx.player.min_peers,
        ),
    ]
    if rule.possession_variant:
        analyses.append(_possession_analysis(ctx, mv.values, subject_id, rule))
    analyses += [
        _metric_variant_analysis(ctx, name, subject_id, rule) for name in rule.variant_metrics
    ]

    main = analyses[0]
    if main.verdict is None:
        return ClaimResult(claim, Verdict.INSUFFICIENT_DATA, etype, main.detail, tuple(analyses))
    evaluable = [a.verdict for a in analyses if a.verdict is not None]
    final = weakest_league(evaluable)
    events = float(mv.events[subject_id])
    summary = f"{main.data['value']:.2f} {metric.unit} ({events:g} in {minutes} min); {main.detail}"
    if final != main.verdict:
        summary += "; a sensitivity analysis lowers the verdict"
    return ClaimResult(claim, final, etype, summary, tuple(analyses))


def _metric_variant_analysis(
    ctx: LeagueContext, name: str, subject_id: str, rule: LeaguePositionRule
) -> Analysis:
    """The same rule with a related metric; never replaces the main metric."""
    label = f"metric:{name}"
    metric = ctx.metrics[name]
    absent = missing_columns(ctx.league, metric)
    if absent:
        return Analysis(label, None, f"not evaluable: source does not provide {', '.join(absent)}")
    mv = compute_metric(ctx.league, metric)
    if subject_id not in mv.values.index:
        reason = mv.excluded.get(subject_id, "no value")
        return Analysis(label, None, f"not evaluable: subject {reason}")
    return _position_analysis(
        label,
        subject_id,
        mv.values,
        _eligible(ctx, ctx.snapshot.min_minutes, subject_id),
        rule,
        ctx.player.min_peers,
    )


def _possession_analysis(
    ctx: LeagueContext, raw: pd.Series, subject_id: str, rule: LeaguePositionRule
) -> Analysis:
    name = "possession_adjusted"
    if ctx.teams is None or "possession_pct" not in ctx.teams.columns:
        return Analysis(name, None, "not evaluable: team possession unavailable")
    team_of = ctx.league.set_index("player_id")["team"]
    possession = ctx.teams.set_index("team")["possession_pct"]
    adjusted, dropped = adjust_for_possession(raw, team_of, possession)
    if subject_id in dropped:
        return Analysis(name, None, "not evaluable: no possession figure for the subject's team")
    analysis = _position_analysis(
        name,
        subject_id,
        adjusted,
        _eligible(ctx, ctx.snapshot.min_minutes, subject_id),
        rule,
        ctx.player.min_peers,
    )
    data = {**analysis.data, "team_possession_pct": float(possession[team_of[subject_id]])}
    return Analysis(analysis.name, analysis.verdict, analysis.detail, data)


# --------------------------------------------------------------------------- Rule V


def proportion_analysis(
    name: str,
    counts: Sequence[MatchCount],
    direction: str,
    threshold: float,
    n_min: int,
    z: float,
) -> Analysis:
    x = sum(c.successes for c in counts)
    n = sum(c.n for c in counts)
    if n < n_min:
        return Analysis(
            name, Verdict.INSUFFICIENT_DATA, f"{x} of {n} (< {n_min} events)", {"x": x, "n": n}
        )
    p = x / n
    lo, hi = wilson_interval(x, n, z)

    def claimed(v: float) -> bool:
        return v > threshold if direction == "greater" else v < threshold

    def opposite(v: float) -> bool:
        return v < threshold if direction == "greater" else v > threshold

    # Leave-one-match-out over matches that contributed events; an empty remainder fails.
    lomo: list[float | None] = []
    for c in counts:
        if c.n == 0:
            continue
        rest = n - c.n
        lomo.append((x - c.successes) / rest if rest > 0 else None)
    lomo_claimed = all(v is not None and claimed(v) for v in lomo)
    lomo_opposite = all(v is not None and opposite(v) for v in lomo)

    claimed_bound = lo if direction == "greater" else hi
    opposite_bound = hi if direction == "greater" else lo
    if claimed(claimed_bound) and lomo_claimed:
        verdict = Verdict.SUPPORTED
    elif opposite(opposite_bound) and lomo_opposite:
        verdict = Verdict.CONTRADICTED
    else:
        verdict = Verdict.INCONCLUSIVE
    lomo_values = [v for v in lomo if v is not None]
    detail = f"{x} of {n} ({p:.0%}); 90% Wilson {lo:.0%}–{hi:.0%}; threshold {threshold:.0%}"
    return Analysis(
        name,
        verdict,
        detail,
        {
            "x": x,
            "n": n,
            "p": p,
            "lo": lo,
            "hi": hi,
            "lomo_min": min(lomo_values) if lomo_values else None,
            "lomo_max": max(lomo_values) if lomo_values else None,
        },
    )


def _video_counts(
    rule: VideoProportionRule, events: pd.DataFrame, match_ids: list[str]
) -> list[tuple[str, list[MatchCount]]]:
    if rule.measure == "open_play_share":
        counts, _unknown = open_play_counts(events, match_ids)
        return [("main", counts)]
    return [
        ("main", tracking_counts(events, match_ids, None)),
        ("ambiguous_as_tracked", tracking_counts(events, match_ids, "tracked")),
        ("ambiguous_as_not_tracked", tracking_counts(events, match_ids, "not_tracked")),
    ]


def evaluate_video(claim: Claim, rule: VideoProportionRule, ctx: VideoContext) -> ClaimResult:
    etype = EvidenceType.VIDEO_ESTIMATE
    p = ctx.player
    analyses = [
        proportion_analysis(name, counts, rule.direction, rule.threshold, p.video_n_min, p.video_z)
        for name, counts in _video_counts(rule, ctx.events, ctx.match_ids)
    ]
    main = analyses[0]
    if main.verdict == Verdict.INSUFFICIENT_DATA:
        return ClaimResult(claim, Verdict.INSUFFICIENT_DATA, etype, main.detail, tuple(analyses))
    evaluable = {
        a.verdict
        for a in analyses
        if a.verdict is not None and a.verdict != Verdict.INSUFFICIENT_DATA
    }
    final = evaluable.pop() if len(evaluable) == 1 else Verdict.INCONCLUSIVE
    summary = main.detail
    if rule.measure == "open_play_share":
        _, unknown = open_play_counts(ctx.events, ctx.match_ids)
        summary += f"; {unknown} with unknown phase excluded"
    if final != main.verdict:
        summary += "; sensitivity analyses disagree"

    subsets = {}
    for sample, ids in ctx.samples.items():
        sub = proportion_analysis(
            sample,
            _video_counts(rule, ctx.events, ids)[0][1],
            rule.direction,
            rule.threshold,
            p.video_n_min,
            p.video_z,
        )
        subsets[sample] = f"{sub.verdict}: {sub.detail}"
    return ClaimResult(claim, final, etype, summary, tuple(analyses), subsets)


# --------------------------------------------------------------------------- Rule M


def match_majority_verdict(k: int, m: int, m_min: int) -> Verdict:
    if m < max(m_min, 2):
        return Verdict.INSUFFICIENT_DATA
    if (k - 1) / (m - 1) > 0.5:
        return Verdict.SUPPORTED
    if k / m < 0.5:
        return Verdict.NOT_SUPPORTED
    return Verdict.INCONCLUSIVE


def evaluate_matches(claim: Claim, rule: MatchMajorityRule, ctx: VideoContext) -> ClaimResult:
    k, m = protest_matches(ctx.events, ctx.match_ids)
    verdict = match_majority_verdict(k, m, ctx.player.match_min)
    summary = f"protests seen in {k} of {m} coded matches"
    if verdict == Verdict.INSUFFICIENT_DATA:
        summary += f" (< {ctx.player.match_min} matches)"
    subsets = {}
    for sample, ids in ctx.samples.items():
        ks, ms = protest_matches(ctx.events, ids)
        subsets[sample] = f"{ks} of {ms} matches"
    analysis = Analysis("main", verdict, summary, {"k": k, "m": m})
    return ClaimResult(claim, verdict, EvidenceType.VIDEO_COUNT, summary, (analysis,), subsets)


# --------------------------------------------------------------------------- dispatch


def evaluate(
    claims: Sequence[Claim], league: LeagueContext | None, video: VideoContext | None
) -> list[ClaimResult]:
    results = []
    for claim in claims:
        rule = claim.rule
        if isinstance(rule, LeaguePositionRule):
            if league is None:
                results.append(
                    ClaimResult(
                        claim,
                        Verdict.UNAVAILABLE,
                        EvidenceType.LEAGUE_POSITION,
                        "no league snapshot",
                    )
                )
            else:
                results.append(evaluate_league(claim, rule, league))
        elif video is None:
            etype = (
                EvidenceType.VIDEO_COUNT
                if isinstance(rule, MatchMajorityRule)
                else EvidenceType.VIDEO_ESTIMATE
            )
            results.append(ClaimResult(claim, Verdict.UNAVAILABLE, etype, "no coded matches"))
        elif isinstance(rule, VideoProportionRule):
            results.append(evaluate_video(claim, rule, video))
        else:
            results.append(evaluate_matches(claim, rule, video))
    return results
