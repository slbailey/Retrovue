Goal: Define provider-agnostic domain + ORM models and first Alembic migration.

Entities (with suggested fields):

- Title(id UUID, kind: 'movie'|'show', name, year?, external_ids JSONB, created_at)
- Season(id UUID, title_id FK, number, created_at)
- Episode(id UUID, title_id FK, season_id FK?, number?, name?, external_ids JSONB, created_at)
- Asset(id UUID, uri TEXT, size BIGINT, duration_ms INT, video_codec?, audio_codec?, container?, hash_sha256, discovered_at, canonical BOOLEAN default false)
- EpisodeAsset(episode_id FK, asset_id FK, PRIMARY KEY(episode_id, asset_id))
- ProviderRef(id UUID, entity_type ENUM['title','episode','asset'], entity_id UUID, provider ENUM['plex','jellyfin','filesystem','manual'], provider_key TEXT, raw JSONB)
- Marker(id UUID, asset_id FK, kind ENUM['chapter','avail','bumper','intro','outro'], start_ms INT, end_ms INT, payload JSONB)
- ReviewQueue(id UUID, asset_id FK, reason TEXT, confidence FLOAT, status ENUM['pending','resolved'], created_at, resolved_at?)

Infra:

- SQLAlchemy 2.x declarative models mirroring above.
- Alembic migration #1 creates these tables.
- Settings: database URL via Pydantic Settings class RETROVUE\_\*.

Acceptance criteria:

- `alembic upgrade head` creates tables.
- mypy passes on models.
- docs/DB_SCHEMA.md explains tables + relationships.

Touch files:

- src/retrovue/infra/db.py (engine/session)
- src/retrovue/infra/migrations/\*\* (alembic init + migration)
- src/retrovue/domain/models.py (dataclasses or Pydantic domain types if useful)
- docs/DB_SCHEMA.md
