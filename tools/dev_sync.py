# tools/dev_sync.py
import sys
import json
import time
import argparse
from typing import Dict, Any

# Adjust these imports to your modules
sys.path.insert(0, 'src')
from retrovue.core.database import RetrovueDatabase as DB
from retrovue.core import plex_integration as pi

def _progress(event: str, payload: Dict[str, Any]):
    if event == "library_start":
        print(f"[START] server={payload['server_id']} library={payload['library_id']}")
    elif event == "page_progress":
        p = payload
        print(f"[PAGE]  server={p['server_id']} lib={p['library_id']} "
              f"processed={p['processed']} changed={p['changed']} skipped={p['skipped']} errors={p['errors']}")
    elif event == "library_done":
        s = payload["summary"]
        print(f"[DONE]  server={payload['server_id']} lib={payload['library_id']} "
              f"+{s['changed']} ~{s['skipped']} !{s['errors']} "
              f"missing↑{s['missing_promoted']} deleted↑{s['deleted_promoted']}")

def main():
    ap = argparse.ArgumentParser(description="Dev sync runner (headless)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--all-selected", action="store_true", help="sync all selected libraries across all servers")
    g.add_argument("--server-selected", type=int, metavar="SERVER_ID", help="sync selected libraries on a server")
    g.add_argument("--library", nargs=2, metavar=("SERVER_ID","SECTION_KEY"), help="sync one library")
    ap.add_argument("--deep", action="store_true", help="force full expand")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true", help="print final summary as JSON")
    ap.add_argument("--db", default="retrovue.db", help="db path or URL")
    args = ap.parse_args()

    db = DB(args.db)
    now = int(time.time())

    summaries = []

    # You likely have helpers in plex_integration for iterating servers/libraries.
    # Here we call into your higher-level functions; adjust names if needed.

    if args.all_selected:
        results = pi.sync_selected_across_all_servers(db, deep=args.deep, dry_run=args.dry_run, progress=_progress)
        summaries.append(results)

    elif args.server_selected is not None:
        server_id = int(args.server_selected)
        results = pi.sync_selected_on_server(db, server_id=server_id, deep=args.deep, dry_run=args.dry_run, progress=_progress)
        summaries.append(results)

    else:  # one library
        sid = int(args.library[0]); section_key = args.library[1]
        # Expect a helper that builds a minimal library ref; change to your type if different
        lib = pi.make_library_ref(db, server_id=sid, section_key=section_key)
        results = pi.sync_one_library(db, lib, deep=args.deep, dry_run=args.dry_run, progress=_progress)
        summaries.append(results)

    if args.json:
        print(json.dumps(summaries, indent=2))

if __name__ == "__main__":
    sys.exit(main())
