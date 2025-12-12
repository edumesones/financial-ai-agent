# backend/tests/conftest.py
"""Pytest configuration and fixtures."""

import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_csv_path():
    """Path to sample CSV file."""
    from pathlib import Path
    return str(Path("tests/fixtures/sample_extracto.csv"))


@pytest.fixture
def sample_transaction():
    """Sample transaction data."""
    return {
        'fecha': '15/12/2024',
        'concepto': 'TRANSFERENCIA NOMINA',
        'importe': '2500.00',
        'referencia': 'REF123'
    }
