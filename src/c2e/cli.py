"""Command line: `c2e validate` and `c2e run`."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from c2e.config import load_metrics
from c2e.contracts import DataContractError
from c2e.pipeline import load_inputs, run
from c2e.report import write_report

app = typer.Typer(add_completion=False, help="Claim-to-Evidence Scouting.")

PlayerDir = Annotated[Path, typer.Argument(help="Folder with player.yaml, claims.yaml, tagging/")]
DataDir = Annotated[
    Path | None, typer.Option(help="Folder with the snapshot CSVs (default: <player>/data)")
]
SnapshotOpt = Annotated[str, typer.Option(help="Snapshot name from player.yaml")]
MetricsOpt = Annotated[Path, typer.Option(help="Metric definitions")]


@app.command()
def validate(
    player_dir: PlayerDir,
    data_dir: DataDir = None,
    snapshot: SnapshotOpt = "v2",
    metrics: MetricsOpt = Path("config/metrics.yaml"),
) -> None:
    """Check configuration and every input table against its contract."""
    try:
        load_inputs(player_dir, data_dir or player_dir / "data", snapshot, metrics)
    except (DataContractError, ValueError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from None
    typer.echo("all inputs valid")


@app.command("run")
def run_cmd(
    player_dir: PlayerDir,
    out: Annotated[Path, typer.Option(help="Output folder")],
    data_dir: DataDir = None,
    snapshot: SnapshotOpt = "v2",
    metrics: MetricsOpt = Path("config/metrics.yaml"),
) -> None:
    """Evaluate every claim and write the evidence report, claims.csv and figures."""
    try:
        inputs = load_inputs(player_dir, data_dir or player_dir / "data", snapshot, metrics)
    except (DataContractError, ValueError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from None
    result = run(inputs)
    path = write_report(result, out)
    for r in result.results:
        typer.echo(f"{r.claim.id:4} {r.verdict.value:20} {r.summary}")
    typer.echo(f"report: {path}")


@app.command("map")
def map_cmd(
    player_dir: PlayerDir,
    out: Annotated[Path, typer.Option(help="PNG file to write")],
    metrics: MetricsOpt = Path("config/metrics.yaml"),
) -> None:
    """Draw the pre-registered claims: report quote → tested statement → evidence."""
    from c2e import viz
    from c2e.config import load_claims, load_player

    player = load_player(player_dir / "player.yaml")
    claims = load_claims(player_dir / "claims.yaml", load_metrics(metrics))
    title = f"{player.name}: from scouting report to testable claims"
    viz.save(viz.claim_map(claims, title, player.video_unavailable_reason), out)
    typer.echo(f"claim map: {out}")
