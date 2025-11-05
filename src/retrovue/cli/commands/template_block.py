"""Template block CLI commands (standalone blocks)."""

from __future__ import annotations

import json

import typer

from ...infra.db import get_sessionmaker
from ...infra.settings import settings
from ...infra.uow import session
from ...usecases import (
    template_block_add as _uc_block_add,
)
from ...usecases import (
    template_block_delete as _uc_block_delete,
)
from ...usecases import (
    template_block_list as _uc_block_list,
)
from ...usecases import (
    template_block_show as _uc_block_show,
)
from ...usecases import (
    template_block_update as _uc_block_update,
)

app = typer.Typer(name="template-block", help="Standalone template block management operations")


def _get_db_context(test_db: bool):
    if not test_db:
        return session()
    use_test_sessionmaker = bool(getattr(settings, "test_database_url", None)) or hasattr(
        get_sessionmaker, "assert_called"
    )
    if use_test_sessionmaker:
        try:
            SessionForTest = get_sessionmaker(for_test=True)
            return SessionForTest()
        except Exception:
            pass
    return session()


@app.command("add")
def add_block(
    name: str | None = typer.Option(None, "--name", help="Block name (unique)"),
    rule_json: str | None = typer.Option(None, "--rule-json", help="Rule JSON string (e.g., '{\"key\": \"value\"}' in PowerShell)"),
    rule_json_file: str | None = typer.Option(None, "--rule-json-file", help="Path to file containing rule JSON"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    test_db: bool = typer.Option(False, "--test-db", help="Use test database context"),
):
    """Create a standalone template block."""
    db_cm = _get_db_context(test_db)

    with db_cm as db:
        try:
            if not name:
                typer.echo("Error: --name is required", err=True)
                raise typer.Exit(1)
            
            # Get rule_json from file or option
            if rule_json_file:
                try:
                    with open(rule_json_file, encoding="utf-8") as f:
                        rule_json = f.read().strip()
                except Exception as e:
                    if json_output:
                        typer.echo(json.dumps({"status": "error", "error": f"Failed to read rule_json_file: {e}"}, indent=2))
                    else:
                        typer.echo(f"Error: Failed to read rule_json_file: {e}", err=True)
                    raise typer.Exit(1)
            
            if not rule_json:
                typer.echo("Error: --rule-json or --rule-json-file is required", err=True)
                raise typer.Exit(1)

            # Try to repair JSON if PowerShell stripped quotes (common issue)
            # PowerShell often strips quotes, turning {"key": "value"} into {key: value}
            try:
                json.loads(rule_json)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to repair common PowerShell quote-stripping issues
                import re
                # Pattern 1: Add quotes around unquoted keys (key: -> "key":)
                repaired = re.sub(
                    r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:',
                    r'\1"\2":',
                    rule_json
                )
                # Pattern 2: Add quotes around unquoted string values in arrays ([value] -> ["value"])
                repaired = re.sub(
                    r'\[\s*([a-zA-Z][a-zA-Z0-9_]*)\s*\]',
                    r'["\1"]',
                    repaired
                )
                # Pattern 3: Add quotes around unquoted string values after colons
                # Handle both quoted strings like "TV-Y7" and unquoted like TV-Y7
                # First, handle string values that look like identifiers (alphanumeric with dashes/underscores)
                repaired = re.sub(
                    r':\s*([a-zA-Z][a-zA-Z0-9_\-]*)\s*([,}])',
                    r': "\1"\2',
                    repaired
                )
                # Pattern 4: Handle numeric values - ensure they stay unquoted
                # (This is handled by the regex above which only matches alphabetic-starting strings)
                try:
                    json.loads(repaired)  # Validate it parses
                    rule_json = repaired
                except json.JSONDecodeError:
                    # If repair still fails, let the original error propagate from the usecase
                    pass

            result = _uc_block_add.add_template_block(
                db,
                name=name,
                rule_json=rule_json,
            )

            if json_output:
                payload = {"status": "ok", "block": result}
                typer.echo(json.dumps(payload, indent=2))
            else:
                typer.echo("Template block created:")
                typer.echo(f"  ID: {result['id']}")
                typer.echo(f"  Name: {result['name']}")
                rule_json_str = json.dumps(result["rule_json"])
                typer.echo(f"  Rule JSON: {rule_json_str}")
                if result.get("created_at"):
                    typer.echo(f"  Created: {result['created_at']}")
            return
        except typer.Exit:
            raise
        except Exception as e:
            if json_output:
                typer.echo(json.dumps({"status": "error", "error": str(e)}, indent=2))
            else:
                typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)


@app.command("update")
def update_block(
    block: str = typer.Option(..., "--block", help="Block (Name or UUID)"),
    name: str | None = typer.Option(None, "--name", help="New block name"),
    rule_json: str | None = typer.Option(None, "--rule-json", help="New rule JSON string"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    test_db: bool = typer.Option(False, "--test-db", help="Use test database context"),
):
    """Update a standalone template block."""
    db_cm = _get_db_context(test_db)

    with db_cm as db:
        try:
            # Check if at least one field is provided
            if name is None and rule_json is None:
                error_msg = "At least one field (--name or --rule-json) must be provided."
                if json_output:
                    typer.echo(json.dumps({"status": "error", "error": error_msg}, indent=2))
                else:
                    typer.echo(f"Error: {error_msg}", err=True)
                raise typer.Exit(1)

            result = _uc_block_update.update_template_block(
                db,
                block=block,
                name=name,
                rule_json=rule_json,
            )

            if json_output:
                payload = {"status": "ok", "block": result}
                typer.echo(json.dumps(payload, indent=2))
            else:
                typer.echo("Template block updated:")
                typer.echo(f"  ID: {result['id']}")
                typer.echo(f"  Name: {result['name']}")
                rule_json_str = json.dumps(result["rule_json"])
                typer.echo(f"  Rule JSON: {rule_json_str}")
            return
        except typer.Exit:
            raise
        except Exception as e:
            if json_output:
                typer.echo(json.dumps({"status": "error", "error": str(e)}, indent=2))
            else:
                typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)


@app.command("delete")
def delete_block(
    block: str = typer.Option(..., "--block", help="Block (Name or UUID)"),
    yes: bool = typer.Option(False, "--yes", help="Confirm deletion (non-interactive)"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    test_db: bool = typer.Option(False, "--test-db", help="Use test database context"),
):
    """Delete a standalone template block."""
    db_cm = _get_db_context(test_db)

    with db_cm as db:
        try:
            if not yes:
                if json_output:
                    typer.echo(
                        json.dumps({"status": "error", "error": "Confirmation required (--yes)"}, indent=2)
                    )
                else:
                    typer.echo("Deletion requires --yes confirmation", err=True)
                raise typer.Exit(1)

            result = _uc_block_delete.delete_template_block(db, block=block)

            if json_output:
                typer.echo(json.dumps({"status": "ok", "deleted": 1, "id": result["id"]}, indent=2))
            else:
                typer.echo(f"Template block deleted: {block}")
            return
        except typer.Exit:
            raise
        except Exception as e:
            if json_output:
                typer.echo(json.dumps({"status": "error", "error": str(e)}, indent=2))
            else:
                typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)


@app.command("list")
def list_blocks(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    test_db: bool = typer.Option(False, "--test-db", help="Use test database context"),
):
    """List all standalone template blocks."""
    db_cm = _get_db_context(test_db)

    with db_cm as db:
        try:
            blocks = _uc_block_list.list_template_blocks(db)

            if json_output:
                payload = {"status": "ok", "total": len(blocks), "blocks": blocks}
                typer.echo(json.dumps(payload, indent=2))
            else:
                if not blocks:
                    typer.echo("No template blocks found")
                else:
                    typer.echo("Template blocks:")
                    for b in blocks:
                        typer.echo(f"  ID: {b['id']}")
                        typer.echo(f"  Name: {b['name']}")
                        rule_json_str = json.dumps(b["rule_json"])
                        typer.echo(f"  Rule JSON: {rule_json_str}")
                        typer.echo("")
                    typer.echo(f"Total: {len(blocks)} blocks")
            return
        except Exception as e:
            if json_output:
                typer.echo(json.dumps({"status": "error", "error": str(e)}, indent=2))
            else:
                typer.echo(f"Error listing blocks: {e}", err=True)
            raise typer.Exit(1)


@app.command("show")
def show_block(
    block: str = typer.Option(..., "--block", help="Block (Name or UUID)"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    test_db: bool = typer.Option(False, "--test-db", help="Use test database context"),
):
    """Show a standalone template block by ID or name."""
    db_cm = _get_db_context(test_db)

    with db_cm as db:
        try:
            result = _uc_block_show.show_template_block(db, block=block)

            if json_output:
                payload = {"status": "ok", "block": result}
                typer.echo(json.dumps(payload, indent=2))
            else:
                typer.echo("Template block:")
                typer.echo(f"  ID: {result['id']}")
                typer.echo(f"  Name: {result['name']}")
                rule_json_str = json.dumps(result["rule_json"])
                typer.echo(f"  Rule JSON: {rule_json_str}")
                if result.get("created_at"):
                    typer.echo(f"  Created: {result['created_at']}")
                if result.get("updated_at"):
                    typer.echo(f"  Updated: {result['updated_at']}")
            return
        except typer.Exit:
            raise
        except Exception as e:
            if json_output:
                typer.echo(json.dumps({"status": "error", "error": str(e)}, indent=2))
            else:
                typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)

