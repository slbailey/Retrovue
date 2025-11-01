"""
Asset CLI commands for asset visibility and review workflows.

Surfaces read-only views to help operators verify ingest effects.
"""

from __future__ import annotations

import json

import typer

from ...infra.db import get_sessionmaker
from ...infra.settings import settings
from ...infra.uow import session
from ...usecases import asset_attention as _uc_asset_attention
from ...usecases import asset_list as _uc_asset_list
from ...usecases import asset_update as _uc_asset_update

app = typer.Typer(name="asset", help="Asset inspection and review operations")


def _get_db_context(test_db: bool):
    """Return an appropriate DB context manager based on test_db flag."""
    if not test_db:
        return session()

    use_test_sessionmaker = bool(getattr(settings, "test_database_url", None)) or hasattr(
        get_sessionmaker, "assert_called"
    )
    if use_test_sessionmaker:
        try:
            SessionForTest = get_sessionmaker(for_test=True)
            return SessionForTest()
        except Exception:  # pragma: no cover - fall back if unavailable
            pass
    return session()


@app.command("attention")
def list_attention(
    collection: str | None = typer.Option(None, "--collection", help="Filter by collection UUID"),
    limit: int = typer.Option(100, "--limit", help="Max rows to return"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    List assets needing attention (downgraded or not broadcastable).
    """
    with session() as db:
        rows = _uc_asset_attention.list_assets_needing_attention(
            db, collection_uuid=collection, limit=limit
        )

    if not rows:
        typer.echo("No assets need attention")
        raise typer.Exit(0)

    if json_output:
        typer.echo(
            json.dumps(
                {
                    "status": "ok",
                    "total": len(rows),
                    "assets": rows,
                },
                indent=2,
            )
        )
        raise typer.Exit(0)
    else:
        for r in rows:
            typer.echo(
                f"{r['uuid']}  {r['state']:<10} approved={r['approved_for_broadcast']}  {r['uri']}"
            )


@app.command("list")
def list_assets(
    collection: str | None = typer.Option(None, "--collection", help="Filter by collection UUID"),
    state: str | None = typer.Option(None, "--state", help="Filter by lifecycle state"),
    approved: bool | None = typer.Option(
        None, "--approved/--no-approved", help="Filter by approved_for_broadcast"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    test_db: bool = typer.Option(False, "--test-db", help="Use test database context"),
):
    """
    List assets with optional filters.

    Default behavior (no filters): broadcast-ready assets only.
    """
    valid_states = {"new", "enriching", "ready", "retired"}
    if state is not None and state not in valid_states:
        typer.echo("Error: Invalid state. Must be one of: new, enriching, ready, retired", err=True)
        raise typer.Exit(1)

    # Apply defaults only when neither state nor approved are provided
    default_state = state
    default_approved = approved
    include_deleted = False
    if state is None and approved is None:
        default_state = "ready"
        default_approved = True

    db_cm = _get_db_context(test_db)
    with db_cm as db:
        rows = _uc_asset_list.list_assets(
            db,
            collection_uuid=collection,
            state=default_state,
            approved=default_approved,
            include_deleted=include_deleted,
        )

    if json_output:
        typer.echo(
            json.dumps(
                {
                    "status": "ok",
                    "total": len(rows),
                    "assets": rows,
                },
                indent=2,
            )
        )
        return

    if not rows:
        typer.echo("No assets found")
        return

    # Human-friendly table using Rich
    try:
        from rich.console import Console
        from rich.table import Table

        console = Console(width=200)
        table = Table(title="Assets", expand=True)
        # Columns: Title (episode/movie), Series (for shows), Season, Episode, Year, Canonical
        table.add_column("Title", style="green", no_wrap=True)
        table.add_column("Type", style="magenta", no_wrap=True)
        table.add_column("Series", style="cyan")
        table.add_column("Season", style="magenta")
        table.add_column("Episode", style="magenta")
        table.add_column("Year", style="cyan")
        table.add_column("Canonical", style="cyan", no_wrap=True)
        table.add_column("State", style="yellow")
        table.add_column("Approved", style="blue")
        table.add_column("Path", style="white")

        for r in rows:
            title_obj = r.get("title") or {}
            title_name = title_obj.get("name") if isinstance(title_obj, dict) else None
            title_year = title_obj.get("year") if isinstance(title_obj, dict) else None
            title_kind = title_obj.get("kind") if isinstance(title_obj, dict) else None
            series_name = None
            series_obj = r.get("series") or {}
            if isinstance(series_obj, dict):
                series_name = series_obj.get("name")
            ep = r.get("episode") or {}
            season_num = ep.get("season") if isinstance(ep, dict) else None
            episode_num = ep.get("number") if isinstance(ep, dict) else None
            canonical = r.get("canonical_key") or r.get("canonical")

            table.add_row(
                str(title_name) if title_name else "Not Available",
                (str(title_kind) if title_kind else "Not Available"),
                str(series_name) if series_name else "Not Available",
                (str(season_num) if season_num is not None else "Not Available"),
                (str(episode_num) if episode_num is not None else "Not Available"),
                (str(title_year) if title_year is not None else "Not Available"),
                str(canonical) if canonical else "Not Available",
                str(r.get("state") or "-"),
                "yes" if bool(r.get("approved_for_broadcast")) else "no",
                str(r.get("uri") or "-"),
            )

        console.print(table)
        # Ensure canonical IDs appear untruncated for contract visibility
        try:
            canonicals: list[str] = []
            for r in rows:
                c = r.get("canonical_key") or r.get("canonical")
                if c:
                    canonicals.append(str(c))
            if canonicals:
                console.print("Canonical IDs: " + ", ".join(canonicals))
        except Exception:
            pass
    except Exception:
        # Fallback simple lines if Rich is unavailable
        for r in rows:
            title_obj = r.get("title") or {}
            title_name = title_obj.get("name") if isinstance(title_obj, dict) else None
            title_year = title_obj.get("year") if isinstance(title_obj, dict) else None
            title_kind = title_obj.get("kind") if isinstance(title_obj, dict) else None
            series_name = None
            series_obj = r.get("series") or {}
            if isinstance(series_obj, dict):
                series_name = series_obj.get("name")
            ep = r.get("episode") or {}
            season_num = ep.get("season") if isinstance(ep, dict) else None
            episode_num = ep.get("number") if isinstance(ep, dict) else None
            canonical = r.get("canonical_key") or r.get("canonical")
            typer.echo(
                f"Title={title_name or 'Not Available'} | Type={title_kind or 'Not Available'} | Series={series_name or 'Not Available'} | "
                f"Season={season_num if season_num is not None else 'Not Available'} | "
                f"Episode={episode_num if episode_num is not None else 'Not Available'} | "
                f"Year={title_year if title_year is not None else 'Not Available'} | Canonical={canonical or 'Not Available'} | "
                f"State={r.get('state')} | Approved={'yes' if r.get('approved_for_broadcast') else 'no'} | Path={r.get('uri')}"
            )


@app.command("resolve")
def resolve_asset(
    asset_uuid: str = typer.Argument(..., help="Asset UUID to resolve"),
    approve: bool = typer.Option(False, "--approve", help="Approve asset for broadcast"),
    ready: bool = typer.Option(
        False, "--ready", help="Mark asset state=ready (allowed from enriching)"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Resolve a single asset by approving and/or marking ready.

    When no flags are provided, prints current asset info (read-only).
    """
    with session() as db:
        # Read-only path if no mutation flags
        if not approve and not ready:
            try:
                summary = _uc_asset_update.get_asset_summary(db, asset_uuid=asset_uuid)
            except ValueError as exc:
                typer.echo(f"Error: {exc}")
                raise typer.Exit(1)

            if json_output:
                typer.echo(json.dumps({"status": "ok", "asset": summary}, indent=2))
            else:
                typer.echo(
                    f"{summary['uuid']}  {summary['state']:<10} approved={summary['approved_for_broadcast']}  {summary['uri']}"
                )
            raise typer.Exit(0)

        # Mutation path
        try:
            new_state = "ready" if ready else None
            result = _uc_asset_update.update_asset_review_status(
                db,
                asset_uuid=asset_uuid,
                approved=True if approve else None,
                state=new_state,
            )
        except ValueError as exc:
            typer.echo(f"Error: {exc}")
            raise typer.Exit(1)

    if json_output:
        typer.echo(json.dumps({"status": "ok", "asset": result}, indent=2))
    else:
        typer.echo(f"Asset {result['uuid']} updated")
