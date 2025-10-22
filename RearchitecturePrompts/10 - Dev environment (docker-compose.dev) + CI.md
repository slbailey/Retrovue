Goal: Reproducible dev and minimal CI.

Add:

- docker-compose.dev.yml with services:
  - api (uvicorn), worker (if needed later), postgres, redis (future), app volume mount
- .env.example with RETROVUE_DB_URL, RETROVUE_MEDIA_ROOTS, PLEX_TOKEN, etc.
- GitHub Actions:
  - python-app.yml: setup Python, install deps, ruff, mypy, pytest (sqlite), build docs links check
- Makefile or just pyproject scripts for: lint, type, test, run

Acceptance criteria:

- `docker compose -f docker-compose.dev.yml up` starts Postgres + API.
- CI passes: lint + type + tests.
- README includes a “Dev in 60 seconds” section.

Touch files:

- docker-compose.dev.yml
- .env.example
- .github/workflows/python-app.yml
- README.md
