"""CLI package for Retrovue."""

from .main import app, cli

__all__ = ["app", "cli"]

# For direct execution without module import warnings
if __name__ == "__main__":
    cli()
