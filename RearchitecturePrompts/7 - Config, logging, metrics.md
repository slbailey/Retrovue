Goal: Standardize settings, logging, and stubs for metrics.

Implement:

- src/retrovue/infra/settings.py (Pydantic Settings)
  - RETROVUE_DB_URL, RETROVUE_MEDIA_ROOTS, RETROVUE_LOG_LEVEL, RETROVUE_PROVIDER_PLEX_TOKEN, etc.
- src/retrovue/infra/logging.py (structlog config; redact secrets)
- src/retrovue/api/routers/health.py
  - GET /healthz returns {status:'ok', version, db:'ok'}
- src/retrovue/api/routers/metrics.py
  - GET /metrics placeholder (Prometheus exposition to be added later)

Acceptance criteria:

- All components import Settings via a single module function.
- Logs appear in JSON with request_id when API is called.
- Secrets are not printed in logs.

Touch files:

- src/retrovue/infra/settings.py
- src/retrovue/infra/logging.py
- src/retrovue/api/routers/{health.py,metrics.py}
