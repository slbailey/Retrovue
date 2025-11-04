"""
CLI Router: Centralized command group registration and dispatch.

This module provides a router-based abstraction for registering and organizing
CLI command groups. Each command group is a Typer app that handles its own
subcommands and arguments.

The router ensures:
- Domain ownership is clear (each command group owns its domain)
- Command registration is explicit and discoverable
- CLI structure is documented and maintainable
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import typer

if TYPE_CHECKING:
    from typing import Any


class CliRouter:
    """
    Centralized router for CLI command groups.
    
    Provides explicit registration of command groups with documentation mapping.
    Each command group is a Typer app that handles its own subcommands.
    """

    def __init__(self, root_app: typer.Typer) -> None:
        """
        Initialize the router with a root Typer application.
        
        Args:
            root_app: The root Typer application that will receive registered commands
        """
        self.root_app = root_app
        self._registered_groups: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        command_group: typer.Typer,
        *,
        help_text: str | None = None,
        doc_path: str | None = None,
    ) -> None:
        """
        Register a command group with the router.
        
        Args:
            name: Command group name (e.g., "channel", "source")
            command_group: Typer app instance for this command group
            help_text: Help text for the command group
            doc_path: Path to documentation file (relative to docs/cli/)
        """
        if name in self._registered_groups:
            raise ValueError(f"Command group '{name}' is already registered")

        # Register with Typer
        self.root_app.add_typer(command_group, name=name, help=help_text)

        # Track registration metadata
        self._registered_groups[name] = {
            "name": name,
            "help": help_text,
            "doc_path": doc_path,
            "command_group": command_group,
        }

    def get_registered_groups(self) -> dict[str, dict[str, Any]]:
        """
        Get all registered command groups.
        
        Returns:
            Dictionary mapping command group names to their metadata
        """
        return self._registered_groups.copy()

    def list_registered_groups(self) -> list[str]:
        """
        List all registered command group names.
        
        Returns:
            List of registered command group names in registration order
        """
        return list(self._registered_groups.keys())


# Global router instance
_router: CliRouter | None = None


def get_router(root_app: typer.Typer) -> CliRouter:
    """
    Get or create the global CLI router instance.
    
    Args:
        root_app: The root Typer application
        
    Returns:
        CliRouter instance
    """
    global _router
    if _router is None:
        _router = CliRouter(root_app)
    return _router

