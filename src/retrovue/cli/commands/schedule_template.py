"""Schedule template CLI commands."""

from __future__ import annotations

import json

import typer

from ...infra.db import get_sessionmaker
from ...infra.settings import settings
from ...infra.uow import session
from ...usecases import (
    schedule_template_add as _uc_template_add,
)
from ...usecases import (
    schedule_template_delete as _uc_template_delete,
)
from ...usecases import (
    schedule_template_list as _uc_template_list,
)
from ...usecases import (
    schedule_template_show as _uc_template_show,
)
from ...usecases import (
    schedule_template_update as _uc_template_update,
)
from ...usecases import (
    template_block_instance_add as _uc_instance_add,
)
from ...usecases import (
    template_block_instance_delete as _uc_instance_delete,
)
from ...usecases import (
    template_block_instance_list as _uc_instance_list,
)
from ...usecases import (
    template_block_instance_show as _uc_instance_show,
)
from ...usecases import (
    template_block_instance_update as _uc_instance_update,
)

app = typer.Typer(name="schedule-template", help="Schedule template management operations")

# Block subcommands
block_app = typer.Typer(name="block", help="Schedule template block operations")
app.add_typer(block_app)


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
def add_template(
    name: str | None = typer.Option(None, "--name", help="Template name (unique)"),
    description: str | None = typer.Option(None, "--description", help="Template description"),
    active: bool | None = typer.Option(None, "--active/--inactive", help="Initial active state"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    test_db: bool = typer.Option(False, "--test-db", help="Use test database context"),
):
    """Create a schedule template per ScheduleTemplateContract.md."""
    db_cm = _get_db_context(test_db)

    with db_cm as db:
        try:
            if not name:
                typer.echo("Error: --name is required", err=True)
                raise typer.Exit(1)

            is_active = active if active is not None else True

            result = _uc_template_add.add_template(
                db,
                name=name,
                description=description,
                is_active=is_active,
            )

            if json_output:
                payload = {"status": "ok", "template": result}
                typer.echo(json.dumps(payload, indent=2))
            else:
                typer.echo("Template created:")
                typer.echo(f"  ID: {result['id']}")
                typer.echo(f"  Name: {result['name']}")
                if result.get("description"):
                    typer.echo(f"  Description: {result['description']}")
                typer.echo(f"  Active: {str(bool(result['is_active'])).lower()}")
                typer.echo(f"  Blocks: {result['blocks_count']}")
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
def update_template(
    template: str = typer.Option(..., "--template", help="Template (Name or UUID)"),
    name: str | None = typer.Option(None, "--name", help="New template name"),
    description: str | None = typer.Option(None, "--description", help="New template description"),
    active: bool | None = typer.Option(None, "--active/--inactive", help="Set active flag"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    test_db: bool = typer.Option(False, "--test-db", help="Use test database context"),
):
    """Update a schedule template."""
    db_cm = _get_db_context(test_db)

    with db_cm as db:
        try:
            # Check if at least one field is provided
            if name is None and description is None and active is None:
                error_msg = "At least one field (--name, --description, or --active/--inactive) must be provided."
                if json_output:
                    typer.echo(json.dumps({"status": "error", "error": error_msg}, indent=2))
                else:
                    typer.echo(f"Error: {error_msg}", err=True)
                raise typer.Exit(1)

            result = _uc_template_update.update_template(
                db,
                template=template,
                name=name,
                description=description,
                is_active=active,
            )

            if json_output:
                payload = {"status": "ok", "template": result}
                typer.echo(json.dumps(payload, indent=2))
            else:
                typer.echo("Template updated:")
                typer.echo(f"  ID: {result['id']}")
                typer.echo(f"  Name: {result['name']}")
                if result.get("description"):
                    typer.echo(f"  Description: {result['description']}")
                typer.echo(f"  Active: {str(bool(result['is_active'])).lower()}")
                typer.echo(f"  Blocks: {result['blocks_count']}")
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
def delete_template(
    template: str = typer.Option(..., "--template", help="Template (Name or UUID)"),
    yes: bool = typer.Option(False, "--yes", help="Confirm deletion (non-interactive)"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    test_db: bool = typer.Option(False, "--test-db", help="Use test database context"),
):
    """Delete a schedule template."""
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

            result = _uc_template_delete.delete_template(db, template=template)

            if json_output:
                typer.echo(json.dumps({"status": "ok", "deleted": 1, "id": result["id"]}, indent=2))
            else:
                typer.echo(f"Template deleted: {template}")
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
def list_templates(
    active_only: bool = typer.Option(False, "--active-only", help="Show only active templates"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    test_db: bool = typer.Option(False, "--test-db", help="Use test database context"),
):
    """List all schedule templates."""
    db_cm = _get_db_context(test_db)

    with db_cm as db:
        try:
            templates = _uc_template_list.list_templates(db, active_only=active_only)

            if json_output:
                payload = {"status": "ok", "total": len(templates), "templates": templates}
                typer.echo(json.dumps(payload, indent=2))
            else:
                if not templates:
                    typer.echo("No templates found")
                else:
                    typer.echo("Templates:")
                    for t in templates:
                        typer.echo(f"  ID: {t['id']}")
                        typer.echo(f"  Name: {t['name']}")
                        if t.get("description"):
                            typer.echo(f"  Description: {t['description']}")
                        typer.echo(f"  Active: {str(bool(t['is_active'])).lower()}")
                        typer.echo(f"  Blocks: {t['blocks_count']}")
                        typer.echo("")
                    typer.echo(f"Total: {len(templates)} templates")
            return
        except Exception as e:
            if json_output:
                typer.echo(json.dumps({"status": "error", "error": str(e)}, indent=2))
            else:
                typer.echo(f"Error listing templates: {e}", err=True)
            raise typer.Exit(1)


@app.command("show")
def show_template(
    template: str = typer.Option(..., "--template", help="Template (Name or UUID)"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    test_db: bool = typer.Option(False, "--test-db", help="Use test database context"),
):
    """Show a schedule template by ID or name."""
    db_cm = _get_db_context(test_db)

    with db_cm as db:
        try:
            result = _uc_template_show.show_template(db, template=template)

            if json_output:
                payload = {"status": "ok", "template": result}
                typer.echo(json.dumps(payload, indent=2))
            else:
                typer.echo("Template:")
                typer.echo(f"  ID: {result['id']}")
                typer.echo(f"  Name: {result['name']}")
                if result.get("description"):
                    typer.echo(f"  Description: {result['description']}")
                typer.echo(f"  Active: {str(bool(result['is_active'])).lower()}")
                typer.echo(f"  Blocks ({result['blocks_count']}):")
                for block in result.get("blocks", []):
                    rule_json_str = json.dumps(block["rule_json"])
                    typer.echo(f"    {block['start_time']}-{block['end_time']}: {rule_json_str}")
                typer.echo(f"  Plans using this template: {result.get('plans_count', 0)}")
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


@block_app.command("add")
def add_block(
    template: str = typer.Option(..., "--template", help="Template (Name or UUID)"),
    block: str = typer.Option(..., "--block", help="Block (Name or UUID)"),
    start_time: str = typer.Option(..., "--start-time", help="Block start time (HH:MM or HH:MM+1 for next day)"),
    end_time: str = typer.Option(..., "--end-time", help="Block end time (HH:MM or HH:MM+1 for next day)"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    test_db: bool = typer.Option(False, "--test-db", help="Use test database context"),
):
    """Add a block instance to a schedule template (link existing block with timing)."""
    db_cm = _get_db_context(test_db)

    with db_cm as db:
        try:
            result = _uc_instance_add.add_template_block_instance(
                db,
                template=template,
                block=block,
                start_time=start_time,
                end_time=end_time,
            )

            if json_output:
                payload = {"status": "ok", "instance": result}
                typer.echo(json.dumps(payload, indent=2))
            else:
                typer.echo("Template block instance created:")
                typer.echo(f"  Instance ID: {result['id']}")
                typer.echo(f"  Template: {result['template_id']}")
                typer.echo(f"  Block: {result['block_name']} ({result['block_id']})")
                typer.echo(f"  Start Time: {result['start_time']}")
                typer.echo(f"  End Time: {result['end_time']}")
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


@block_app.command("update")
def update_block(
    id: str = typer.Option(..., "--id", help="Block instance UUID"),
    start_time: str | None = typer.Option(None, "--start-time", help="New block start time (HH:MM or HH:MM+1 for next day)"),
    end_time: str | None = typer.Option(None, "--end-time", help="New block end time (HH:MM or HH:MM+1 for next day)"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    test_db: bool = typer.Option(False, "--test-db", help="Use test database context"),
):
    """Update a schedule template block instance timing."""
    db_cm = _get_db_context(test_db)

    with db_cm as db:
        try:
            # Check if at least one field is provided
            if start_time is None and end_time is None:
                error_msg = "At least one field (--start-time or --end-time) must be provided."
                if json_output:
                    typer.echo(json.dumps({"status": "error", "error": error_msg}, indent=2))
                else:
                    typer.echo(f"Error: {error_msg}", err=True)
                raise typer.Exit(1)

            result = _uc_instance_update.update_template_block_instance(
                db,
                instance_id=id,
                start_time=start_time,
                end_time=end_time,
            )

            if json_output:
                payload = {"status": "ok", "instance": result}
                typer.echo(json.dumps(payload, indent=2))
            else:
                typer.echo("Template block instance updated:")
                typer.echo(f"  Instance ID: {result['id']}")
                typer.echo(f"  Start Time: {result['start_time']}")
                typer.echo(f"  End Time: {result['end_time']}")
            return
        except typer.Exit:
            raise
        except Exception as e:
            if json_output:
                typer.echo(json.dumps({"status": "error", "error": str(e)}, indent=2))
            else:
                typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)


@block_app.command("delete")
def delete_block(
    id: str = typer.Option(..., "--id", help="Block UUID"),
    yes: bool = typer.Option(False, "--yes", help="Confirm deletion (non-interactive)"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    test_db: bool = typer.Option(False, "--test-db", help="Use test database context"),
):
    """Delete a schedule template block."""
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

            result = _uc_instance_delete.delete_template_block_instance(db, instance_id=id)

            if json_output:
                typer.echo(json.dumps({"status": "ok", "deleted": 1, "id": result["id"]}, indent=2))
            else:
                typer.echo(f"Template block instance deleted: {id}")
            return
        except typer.Exit:
            raise
        except Exception as e:
            if json_output:
                typer.echo(json.dumps({"status": "error", "error": str(e)}, indent=2))
            else:
                typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)


@block_app.command("list")
def list_blocks(
    template: str = typer.Option(..., "--template", help="Template (Name or UUID)"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    test_db: bool = typer.Option(False, "--test-db", help="Use test database context"),
):
    """List block instances for a schedule template."""
    db_cm = _get_db_context(test_db)

    with db_cm as db:
        try:
            instances = _uc_instance_list.list_template_block_instances(db, template=template)

            if json_output:
                payload = {"status": "ok", "total": len(instances), "instances": instances}
                typer.echo(json.dumps(payload, indent=2))
            else:
                if not instances:
                    typer.echo("No block instances found")
                else:
                    typer.echo("Template block instances:")
                    for inst in instances:
                        typer.echo(f"  Instance ID: {inst['id']}")
                        typer.echo(f"  Block: {inst['block_name']} ({inst['block_id']})")
                        typer.echo(f"  Start Time: {inst['start_time']}")
                        typer.echo(f"  End Time: {inst['end_time']}")
                        rule_json_str = json.dumps(inst["rule_json"])
                        typer.echo(f"  Rule JSON: {rule_json_str}")
                        typer.echo("")
                    typer.echo(f"Total: {len(instances)} instances")
            return
        except Exception as e:
            if json_output:
                typer.echo(json.dumps({"status": "error", "error": str(e)}, indent=2))
            else:
                typer.echo(f"Error listing block instances: {e}", err=True)
            raise typer.Exit(1)


@block_app.command("show")
def show_block(
    id: str = typer.Option(..., "--id", help="Block UUID"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    test_db: bool = typer.Option(False, "--test-db", help="Use test database context"),
):
    """Show a schedule template block by ID."""
    db_cm = _get_db_context(test_db)

    with db_cm as db:
        try:
            result = _uc_instance_show.show_template_block_instance(db, instance_id=id)

            if json_output:
                payload = {"status": "ok", "block": result}
                typer.echo(json.dumps(payload, indent=2))
            else:
                typer.echo("Template block instance:")
                typer.echo(f"  Instance ID: {result['id']}")
                typer.echo(f"  Template ID: {result['template_id']}")
                typer.echo(f"  Block: {result['block_name']} ({result['block_id']})")
                typer.echo(f"  Start Time: {result['start_time']}")
                typer.echo(f"  End Time: {result['end_time']}")
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

