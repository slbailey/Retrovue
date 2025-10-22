Goal: Build a provider-agnostic ingest pipeline that: discover -> register -> enrich -> review-if-needed -> commit.

Create:

- src/retrovue/app/ingest_pipeline.py

  - run(source: str, enrichers: list[str] = ['ffprobe']) -> summary(dict)
    Steps:
    1. items = importer.discover()
    2. for each item: register_asset_from_discovery()
    3. run enrichers in order; accumulate confidence
    4. if low-confidence mapping to episode/title, enqueue_review()
    5. mark_asset_canonical() if sufficient data

- Confidence heuristic:
  - +0.6 if duration present, +0.2 if codecs present, +0.2 if episode link known
  - threshold: canonical >= 0.8 else review

API endpoints:

- POST /ingest/run?source=plex|filesystem
- GET /review/queue
- POST /review/{id}/resolve (payload: episode_id, title_id?, notes)

Acceptance criteria:

- Endpoint exists and returns JSON summary with counts: discovered, registered, enriched, canonicalized, queued_for_review.
- Review queue endpoints create/update ReviewQueue rows.

Touch files:

- src/retrovue/app/ingest_pipeline.py
- src/retrovue/api/routers/ingest.py
- src/retrovue/api/routers/review.py
- tests/api/test_ingest.py
