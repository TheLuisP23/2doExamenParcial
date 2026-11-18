"""Configuración solo por entorno (REQ-SYS-005): falla al arrancar si falta SERVICE_A_DATABASE_URL."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SERVICE_A_", extra="ignore")

    database_url: str
    port: int = 8000
    log_level: str = "INFO"
    db_pool_size: int = 5
    ready_timeout_s: int = 2
