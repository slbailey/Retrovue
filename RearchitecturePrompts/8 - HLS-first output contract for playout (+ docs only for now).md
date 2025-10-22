Goal: Document the HLS-first decision and align quick-start examples. (No engine refactor yet.)

Docs changes:

- Update README quick-start to reference HLS index.m3u8 endpoints instead of .ts.
- Add docs/PLAYOUT.md with the target:
  - HLS (-f hls, -hls_time 2, -hls_list_size 5, -hls_flags delete_segments+program_date_time)
  - As-run logs alignment via PROGRAM-DATE-TIME
  - Bumpers/ads come from Marker(kind='avail'|'bumper') in Assets

Acceptance criteria:

- README links resolve and show HLS URLs.
- PLAYOUT.md committed with command examples (ffmpeg stub, VLC test).

Touch files:

- README.md
- docs/PLAYOUT.md
