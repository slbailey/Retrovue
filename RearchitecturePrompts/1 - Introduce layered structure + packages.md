Goal: Introduce layered architecture folders with minimal code stubs, keeping current functionality intact.

Create packages:

- src/retrovue/app/ # application services (business use-cases)
- src/retrovue/domain/ # entities, value-objects, domain events
- src/retrovue/adapters/ # importers, enrichers, storage, providers
- src/retrovue/infra/ # db (sqlalchemy), migrations (alembic), logging, settings
- src/retrovue/api/ # FastAPI routers, dependencies
- src/retrovue/cli/ # Typer CLI commands that call app services
- src/retrovue/shared/ # types, utils

Also add: docs/ARCHITECTURE.md (short overview + diagram).

Acceptance criteria:

- New folders + **init**.py files + todo stubs compile.
- Existing code still imports; if needed, add temporary re-exports so current imports don’t break.
- Add pyproject.toml updates (ruff, mypy configs if missing).
- Add scripts: 'dev' (uvicorn), 'lint', 'type', 'test'.

Touch files:

- src/\*\* as above
- pyproject.toml
- docs/ARCHITECTURE.md
