"""Pytest configuration for backend tests."""

import pytest


@pytest.fixture(autouse=True)
def anyio_backend():
    """Use asyncio as the async backend for tests."""
    return "asyncio"
