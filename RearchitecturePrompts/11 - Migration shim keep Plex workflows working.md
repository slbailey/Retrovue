Goal: Ensure existing Plex-based commands still function by routing through new services.

Tasks:

- Wrap legacy Plex fetch/parse code inside PlexImporter (adapters/importers/plex_importer.py).
- Replace any direct DB writes in legacy paths with calls to app.library_service functions.
- Add deprecation warnings (once) if old internal functions are called directly.

Acceptance criteria:

- Running a previous “plex ingest” path yields identical or better outcomes.
- No direct SQLAlchemy session usage remains in legacy modules.
- Unit test proves PlexImporter returns DiscoveredItem list.

Touch files:

- src/retrovue/adapters/importers/plex_importer.py
- any legacy plex modules (minimally edited)
- tests/adapters/test_plex_importer.py
