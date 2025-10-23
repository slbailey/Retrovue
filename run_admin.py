#!/usr/bin/env python3
from __future__ import annotations

import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SRC_DIR = (REPO_ROOT / "src").resolve()

def main() -> None:
    # sanity: make sure package layout exists
    pkg_ok = (SRC_DIR / "retrovue" / "__init__.py").exists() and \
             (SRC_DIR / "retrovue" / "api" / "__init__.py").exists()
    if not pkg_ok:
        print("[run_admin] ERROR: expected package files not found:")
        print(f"  {SRC_DIR / 'retrovue' / '__init__.py'}")
        print(f"  {SRC_DIR / 'retrovue' / 'api' / '__init__.py'}")
        sys.exit(1)

    # Build the exact command we want to run in a fresh process
    cmd = [
        sys.executable, "-m", "uvicorn",
        "retrovue.api.main:app",
        "--app-dir", str(SRC_DIR),
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload",
        "--log-level", "info",
    ]

    print("[run_admin] Launching:", " ".join(cmd))
    try:
        # Run uvicorn as a module (avoids import path weirdness in this process)
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print("\n[run_admin] ERROR: Could not execute Python or uvicorn.")
        print("Make sure your venv is active and uvicorn is installed:")
        print("  .\\venv\\Scripts\\Activate.ps1")
        print('  python -m pip install "uvicorn[standard]" fastapi jinja2 python-multipart')
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\n[run_admin] ERROR: uvicorn exited with code {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
