"""
Retrovue CLI Entry Point

This module provides the main entry point for the Retrovue CLI when run as a module:
    python -m retrovue discover --title "Battlestar Galactica" --year 1978
    python -m retrovue sync --title "Battlestar Galactica" --year 2003
    python -m retrovue sync-all
"""

from .core.cli import main

if __name__ == '__main__':
    main()
