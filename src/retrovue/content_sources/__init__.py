"""
Content Sources Framework

Unified system for managing different content sources that feed into a single content library.
"""

from .registry import registry
from .base import BaseContentSource, ContentSourceCapabilities, ContentSourceConfig

__all__ = ['registry', 'BaseContentSource', 'ContentSourceCapabilities', 'ContentSourceConfig']
