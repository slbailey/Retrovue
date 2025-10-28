"""
Global test configuration for RetroVue.

This module provides global pytest configuration and fixtures.
"""

import pytest


def pytest_ignore_collect(collection_path, config):
    """
    Ignore collection of test files in the _legacy directory.
    
    This ensures that legacy tests are never collected or run,
    preventing import errors from outdated modules.
    """
    if "_legacy" in str(collection_path):
        return True
    return False
