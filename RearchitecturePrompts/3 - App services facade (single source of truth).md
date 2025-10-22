Goal: Add application service methods that own DB writes and workflows. CLI must no longer talk to DB directly.

Create service modules:

- src/retrovue/app/library_service.py

  - register_asset_from_discovery(item) -> Asset
  - enrich_asset(asset_id, enrichment_payload) -> Asset
  - link_asset_to_episode(asset_id, episode_key or episode_id) -> EpisodeAsset
  - mark_asset_canonical(asset_id) -> Asset
  - enqueue_review(asset_id, reason, confidence)
  - list_assets(status?: 'pending'|'canonical')

- src/retrovue/app/ingest_service.py
  - run_ingest(source_name: str) -> summary
  - rescan_asset(asset_id)

Implementation:

- Use SQLAlchemy sessions; no direct DB in CLI/API.
- Emit structlog entries with {asset_id, stage, provider}.

Acceptance criteria:

- Unit tests for:
  - register_asset_from_discovery() creates Asset with hash and uri.
  - link_asset_to_episode() creates EpisodeAsset.
  - enqueue_review() adds ReviewQueue row.

Touch files:

- src/retrovue/app/\*.py
- tests/app/test_library_service.py (write minimal tests)
