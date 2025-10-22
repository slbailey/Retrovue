Goal: Create stable plugin protocols + registry. Wrap existing Plex logic as PlexImporter. Add FilesystemImporter + FFprobeEnricher.

Interfaces:

- src/retrovue/adapters/importers/base.py

  - class Importer(Protocol):
    name: str
    def discover(self) -> list[DiscoveredItem]: ...
  - DiscoveredItem: path_uri, provider_key?, raw_labels?, last_modified

- src/retrovue/adapters/enrichers/base.py

  - class Enricher(Protocol):
    name: str
    def enrich(self, asset: Asset) -> Asset: ...

- src/retrovue/adapters/registry.py
  - register_importer(i: Importer), get_importer(name)
  - register_enricher(e: Enricher), list_enrichers()

Implementations:

- src/retrovue/adapters/importers/plex_importer.py # Wrap existing Plex code; DO NOT delete legacy code; call it internally.
- src/retrovue/adapters/importers/filesystem_importer.py

  - Input: root path(s), glob patterns
  - Output: DiscoveredItem with uri=file:// form, last_modified via stat

- src/retrovue/adapters/enrichers/ffprobe_enricher.py
  - Shell out to ffprobe (if available) or use python-ffmpeg wrapper
  - Populate duration, container, video/audio codecs, stream info
  - Extract chapter markers if present (store as Marker rows)

Acceptance criteria:

- `registry.get_importer('plex')` returns the wrapper around existing logic.
- `registry.get_importer('filesystem')` works on a temp directory in tests.
- `ffprobe_enricher` populates duration and at least one codec in tests (mock ffprobe output ok).

Touch files:

- src/retrovue/adapters/\*\* as above
- tests/adapters/test_filesystem_importer.py
- tests/adapters/test_ffprobe_enricher.py
