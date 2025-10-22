Goal: Give FilesystemImporter a filename parser and feed confidence to the pipeline.

Implement:

- A simple parser for patterns:
  - "Show.Name.S02E05.\*"
  - "Show Name - S2E5 - Episode Title.\*"
  - "Movie.Name.1987.\*"
- Return DiscoveredItem.raw_labels = {title_guess, season?, episode?, year?}
- In ingest_pipeline, compute confidence:
  - +0.4 title match
  - +0.2 season/episode structured
  - +0.2 duration present
  - +0.2 codecs present
  - canonical if >= 0.8 else enqueue review

Add tests for parser with 6 examples.

Files:

- src/retrovue/adapters/importers/filesystem_importer.py
- tests/adapters/test_filename_parser.py
