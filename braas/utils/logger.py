"""
BRaaS Structured Logging
==========================

Configures structured logging via structlog with JSON output,
correlation ID propagation, and experiment-aware context binding.

Usage:
    from braas.utils.logger import setup_logging, get_logger

    setup_logging(level="INFO")
    logger = get_logger("my_module")
    logger.info("processing", experiment_id="abc123")
"""

from __future__ import annotations

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

import structlog

# Context variable for correlation ID propagation across async tasks
_correlation_id_var: ContextVar[str | None] = ContextVar(
    "braas_correlation_id", default=None
)
_experiment_id_var: ContextVar[str | None] = ContextVar(
    "braas_experiment_id", default=None
)


def get_correlation_id() -> str:
    """Get the current correlation ID, generating one if absent."""
    cid = _correlation_id_var.get()
    if cid is None:
        cid = uuid.uuid4().hex
        _correlation_id_var.set(cid)
    return cid


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current async context."""
    _correlation_id_var.set(correlation_id)


def get_experiment_id() -> str | None:
    """Get the current experiment ID from context."""
    return _experiment_id_var.get()


def set_experiment_id(experiment_id: str | None) -> None:
    """Set the experiment ID for the current async context."""
    _experiment_id_var.set(experiment_id)


def _add_correlation_id(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Structlog processor that injects the correlation ID."""
    if "correlation_id" not in event_dict:
        event_dict["correlation_id"] = get_correlation_id()
    return event_dict


def _add_experiment_id(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Structlog processor that injects the experiment ID if set."""
    if "experiment_id" not in event_dict:
        exp_id = get_experiment_id()
        if exp_id is not None:
            event_dict["experiment_id"] = exp_id
    return event_dict


def _add_service_info(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add service metadata to every log entry."""
    event_dict.setdefault("service", "braas-pipeline")
    return event_dict


def setup_logging(
    level: str = "INFO",
    json_output: bool = True,
    log_file: str | None = None,
) -> None:
    """Configure structured logging for the entire application.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_output: If True, output JSON-formatted logs. Otherwise, use
                     colored console output for development.
        log_file: Optional file path to write logs to in addition to stdout.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Shared processors for both structlog and stdlib
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        _add_correlation_id,
        _add_experiment_id,
        _add_service_info,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    # Configure structlog
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to format via structlog
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    # Stdout handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)

    handlers: list[logging.Handler] = [stdout_handler]

    # Optional file handler
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # Apply to root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    for handler in handlers:
        root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Suppress noisy third-party loggers
    for noisy_logger in ("urllib3", "asyncio", "aiohttp", "sqlalchemy.engine"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def get_logger(name: str, **initial_context: Any) -> structlog.stdlib.BoundLogger:
    """Get a structured logger bound to the given name and optional context.

    Args:
        name: Logger name (typically module name).
        **initial_context: Key-value pairs to bind to every log entry.

    Returns:
        A bound structlog logger instance.
    """
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    if initial_context:
        logger = logger.bind(**initial_context)
    return logger


class ExperimentLoggerContext:
    """Context manager that binds experiment and correlation IDs for logging.

    Usage:
        async with ExperimentLoggerContext(experiment_id="abc", correlation_id="xyz"):
            logger.info("doing work")  # auto-includes experiment_id and correlation_id
    """

    def __init__(
        self,
        experiment_id: str,
        correlation_id: str | None = None,
    ) -> None:
        self.experiment_id = experiment_id
        self.correlation_id = correlation_id or uuid.uuid4().hex
        self._prev_experiment_id: str | None = None
        self._prev_correlation_id: str | None = None

    async def __aenter__(self) -> ExperimentLoggerContext:
        self._prev_experiment_id = _experiment_id_var.get()
        self._prev_correlation_id = _correlation_id_var.get()
        set_experiment_id(self.experiment_id)
        set_correlation_id(self.correlation_id)
        return self

    async def __aexit__(self, *args: Any) -> None:
        set_experiment_id(self._prev_experiment_id)
        if self._prev_correlation_id is not None:
            set_correlation_id(self._prev_correlation_id)
        else:
            _correlation_id_var.set(None)
