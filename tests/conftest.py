"""Configuración común de las pruebas transversales (tests/system, tests/platform, tests/smoke)."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "req(*ids): requisitos REQ-* que verifica la prueba (trazabilidad)")


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT
