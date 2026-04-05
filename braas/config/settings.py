"""
BRaaS Application Settings
============================

Centralized configuration using pydantic-settings. Values are loaded
from environment variables with the ``BRAAS_`` prefix. A ``.env`` file
is also supported.

Usage:
    from braas.config import get_settings
    settings = get_settings()
    print(settings.database_url)
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration.

    All fields can be overridden via environment variables prefixed
    with ``BRAAS_`` (e.g., ``BRAAS_DATABASE_URL``).
    """

    model_config = SettingsConfigDict(
        env_prefix="BRAAS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Application ----
    app_name: str = Field(default="BRaaS AI Pipeline", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    environment: str = Field(
        default="development",
        description="Runtime environment (development, staging, production)",
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # ---- Database ----
    database_url: str = Field(
        default="postgresql+asyncpg://braas:braas@localhost:5432/braas",
        description="Primary database connection URL",
    )
    database_pool_size: int = Field(default=20, ge=1, le=200, description="DB connection pool size")
    database_pool_overflow: int = Field(
        default=10, ge=0, le=100, description="Max overflow connections"
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching and task queues",
    )

    # ---- Message Broker ----
    broker_url: str = Field(
        default="amqp://guest:guest@localhost:5672/",
        description="Message broker URL (RabbitMQ/AMQP)",
    )
    event_bus_backend: str = Field(
        default="memory",
        description="Event bus backend: 'memory', 'redis', or 'rabbitmq'",
    )

    # ---- API Keys & Auth ----
    secret_key: str = Field(
        default="CHANGE-ME-IN-PRODUCTION",
        description="Secret key for JWT signing and encryption",
    )
    api_key_header: str = Field(default="X-API-Key", description="API key header name")
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_expiration_minutes: int = Field(
        default=60, ge=1, description="JWT token expiry in minutes"
    )

    # ---- External API Keys ----
    openai_api_key: str = Field(default="", description="OpenAI API key for LLM features")
    ncbi_api_key: str = Field(default="", description="NCBI E-utilities API key")
    uniprot_api_key: str = Field(default="", description="UniProt API key")

    # ---- Lab Equipment Configuration ----
    liquid_handler_host: str = Field(
        default="192.168.1.100", description="Liquid handler controller IP"
    )
    liquid_handler_port: int = Field(
        default=5000, ge=1, le=65535, description="Liquid handler controller port"
    )
    plate_reader_host: str = Field(
        default="192.168.1.101", description="Plate reader controller IP"
    )
    plate_reader_port: int = Field(
        default=5001, ge=1, le=65535, description="Plate reader controller port"
    )
    thermocycler_host: str = Field(
        default="192.168.1.102", description="Thermocycler controller IP"
    )
    thermocycler_port: int = Field(
        default=5002, ge=1, le=65535, description="Thermocycler controller port"
    )
    equipment_timeout_seconds: float = Field(
        default=30.0, gt=0, description="Default equipment communication timeout"
    )
    equipment_retry_count: int = Field(
        default=3, ge=0, le=10, description="Equipment command retry count"
    )

    # ---- ML Model Paths ----
    anomaly_detection_model_path: str = Field(
        default="models/anomaly_detector_v1.onnx",
        description="Path to anomaly detection ONNX model",
    )
    experiment_optimizer_model_path: str = Field(
        default="models/experiment_optimizer_v1.onnx",
        description="Path to experiment optimization model",
    )
    quality_predictor_model_path: str = Field(
        default="models/quality_predictor_v1.onnx",
        description="Path to quality prediction model",
    )
    protocol_generator_model_path: str = Field(
        default="models/protocol_generator_v1",
        description="Path to protocol generation model directory",
    )
    model_cache_dir: str = Field(
        default="/tmp/braas_model_cache",
        description="Directory for caching downloaded models",
    )

    # ---- Storage ----
    data_storage_path: str = Field(
        default="/data/braas", description="Base path for experiment data storage"
    )
    s3_bucket: str = Field(default="braas-data", description="S3 bucket for data storage")
    s3_region: str = Field(default="us-east-1", description="AWS region for S3")
    s3_endpoint_url: str = Field(default="", description="Custom S3 endpoint (MinIO, etc.)")

    # ---- Monitoring ----
    prometheus_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    prometheus_port: int = Field(
        default=9090, ge=1, le=65535, description="Prometheus metrics port"
    )
    sentry_dsn: str = Field(default="", description="Sentry DSN for error tracking")

    # ---- Feature Flags ----
    feature_ai_protocol_generation: bool = Field(
        default=True, description="Enable AI-powered protocol generation"
    )
    feature_anomaly_detection: bool = Field(
        default=True, description="Enable real-time anomaly detection"
    )
    feature_auto_scheduling: bool = Field(
        default=True, description="Enable automated experiment scheduling"
    )
    feature_robot_integration: bool = Field(
        default=False, description="Enable robotic liquid handler integration"
    )
    feature_live_dashboard: bool = Field(
        default=True, description="Enable real-time monitoring dashboard"
    )
    feature_cost_estimation: bool = Field(
        default=True, description="Enable experiment cost estimation"
    )

    # ---- Rate Limits ----
    max_concurrent_experiments: int = Field(
        default=10, ge=1, description="Max experiments running simultaneously"
    )
    max_experiments_per_user_per_day: int = Field(
        default=50, ge=1, description="Rate limit per user per day"
    )

    @field_validator("environment")
    @classmethod
    def _validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production", "testing"}
        if v.lower() not in allowed:
            raise ValueError(f"environment must be one of {allowed}, got '{v}'")
        return v.lower()

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}, got '{v}'")
        return v.upper()

    @property
    def is_production(self) -> bool:
        """Whether running in production environment."""
        return self.environment == "production"

    def get_equipment_config(self, equipment_name: str) -> dict[str, Any]:
        """Get connection config for a specific equipment type.

        Args:
            equipment_name: One of 'liquid_handler', 'plate_reader', 'thermocycler'.

        Returns:
            Dict with 'host', 'port', 'timeout', and 'retries' keys.
        """
        hosts = {
            "liquid_handler": (self.liquid_handler_host, self.liquid_handler_port),
            "plate_reader": (self.plate_reader_host, self.plate_reader_port),
            "thermocycler": (self.thermocycler_host, self.thermocycler_port),
        }
        if equipment_name not in hosts:
            raise ValueError(
                f"Unknown equipment '{equipment_name}'. Known: {list(hosts.keys())}"
            )
        host, port = hosts[equipment_name]
        return {
            "host": host,
            "port": port,
            "timeout": self.equipment_timeout_seconds,
            "retries": self.equipment_retry_count,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings singleton.

    Returns:
        The global Settings instance (created once, then cached).
    """
    return Settings()
