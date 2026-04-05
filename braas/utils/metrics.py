"""
BRaaS Prometheus Metrics
=========================

Defines Prometheus metrics for monitoring the BRaaS pipeline:
experiment throughput, durations, anomalies, equipment utilization,
and ML inference latency.

Usage:
    from braas.utils.metrics import get_metrics

    metrics = get_metrics()
    metrics.experiment_started("elisa", "high")
    with metrics.inference_timer("anomaly_detector"):
        result = model.predict(data)
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Generator

from prometheus_client import Counter, Gauge, Histogram, Info, Summary


class BRaaSMetrics:
    """Centralized Prometheus metrics for the BRaaS pipeline.

    All metrics are prefixed with ``braas_`` for namespace isolation.
    """

    def __init__(self) -> None:
        # ---- Application Info ----
        self.app_info = Info(
            "braas_app",
            "BRaaS application metadata",
        )

        # ---- Experiment Metrics ----
        self.experiment_count = Counter(
            "braas_experiment_total",
            "Total number of experiments processed",
            labelnames=["experiment_type", "status", "priority"],
        )

        self.experiment_created_count = Counter(
            "braas_experiment_created_total",
            "Total experiments created",
            labelnames=["experiment_type"],
        )

        self.experiment_duration_seconds = Histogram(
            "braas_experiment_duration_seconds",
            "Experiment execution duration in seconds",
            labelnames=["experiment_type"],
            buckets=(
                60, 300, 600, 1800, 3600, 7200, 14400,
                28800, 43200, 86400, 172800, 604800,
            ),
        )

        self.active_experiments = Gauge(
            "braas_active_experiments",
            "Number of currently active experiments",
            labelnames=["experiment_type"],
        )

        # ---- Anomaly Metrics ----
        self.anomaly_count = Counter(
            "braas_anomaly_total",
            "Total anomalies detected",
            labelnames=["level", "category", "experiment_type"],
        )

        self.active_anomalies = Gauge(
            "braas_active_anomalies",
            "Currently unresolved anomalies",
            labelnames=["level"],
        )

        self.anomaly_resolution_seconds = Histogram(
            "braas_anomaly_resolution_seconds",
            "Time to resolve anomalies in seconds",
            labelnames=["level"],
            buckets=(30, 60, 300, 600, 1800, 3600, 7200, 14400),
        )

        # ---- Equipment Metrics ----
        self.equipment_utilization = Gauge(
            "braas_equipment_utilization_percent",
            "Equipment utilization percentage",
            labelnames=["equipment_type", "equipment_id"],
        )

        self.equipment_available = Gauge(
            "braas_equipment_available",
            "Number of available equipment units",
            labelnames=["equipment_type"],
        )

        self.equipment_errors = Counter(
            "braas_equipment_errors_total",
            "Equipment communication/operation errors",
            labelnames=["equipment_type", "error_type"],
        )

        # ---- ML/Model Inference Metrics ----
        self.model_inference_latency_seconds = Histogram(
            "braas_model_inference_latency_seconds",
            "ML model inference latency in seconds",
            labelnames=["model_name"],
            buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        )

        self.model_inference_count = Counter(
            "braas_model_inference_total",
            "Total ML model inferences",
            labelnames=["model_name", "status"],
        )

        self.model_prediction_quality = Summary(
            "braas_model_prediction_quality",
            "Model prediction quality scores",
            labelnames=["model_name"],
        )

        # ---- Pipeline Stage Metrics ----
        self.pipeline_stage_duration_seconds = Histogram(
            "braas_pipeline_stage_duration_seconds",
            "Duration of each pipeline stage in seconds",
            labelnames=["stage"],
            buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0),
        )

        self.pipeline_stage_errors = Counter(
            "braas_pipeline_stage_errors_total",
            "Errors per pipeline stage",
            labelnames=["stage", "error_type"],
        )

        # ---- API Metrics ----
        self.api_request_count = Counter(
            "braas_api_requests_total",
            "Total API requests",
            labelnames=["method", "endpoint", "status_code"],
        )

        self.api_request_duration_seconds = Histogram(
            "braas_api_request_duration_seconds",
            "API request duration in seconds",
            labelnames=["method", "endpoint"],
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
        )

        # ---- Scheduling Metrics ----
        self.scheduling_queue_size = Gauge(
            "braas_scheduling_queue_size",
            "Number of experiments in the scheduling queue",
        )

        self.scheduling_wait_seconds = Histogram(
            "braas_scheduling_wait_seconds",
            "Time experiments wait in queue before execution",
            labelnames=["priority"],
            buckets=(60, 300, 900, 1800, 3600, 7200, 14400, 28800, 86400),
        )

    # ---- Convenience Methods ----

    def set_app_info(self, version: str, environment: str) -> None:
        """Set application info gauge.

        Args:
            version: Application version string.
            environment: Runtime environment name.
        """
        self.app_info.info({"version": version, "environment": environment})

    def experiment_started(
        self, experiment_type: str, priority: str = "medium"
    ) -> None:
        """Record that an experiment has started.

        Args:
            experiment_type: The type of experiment.
            priority: Priority level string.
        """
        self.experiment_count.labels(
            experiment_type=experiment_type, status="started", priority=priority
        ).inc()
        self.active_experiments.labels(experiment_type=experiment_type).inc()
        self.experiment_created_count.labels(experiment_type=experiment_type).inc()

    def experiment_completed(
        self,
        experiment_type: str,
        duration_seconds: float,
        priority: str = "medium",
        success: bool = True,
    ) -> None:
        """Record that an experiment has completed.

        Args:
            experiment_type: The type of experiment.
            duration_seconds: Total execution duration.
            priority: Priority level string.
            success: Whether it completed successfully.
        """
        status = "complete" if success else "failed"
        self.experiment_count.labels(
            experiment_type=experiment_type, status=status, priority=priority
        ).inc()
        self.active_experiments.labels(experiment_type=experiment_type).dec()
        self.experiment_duration_seconds.labels(
            experiment_type=experiment_type
        ).observe(duration_seconds)

    def record_anomaly(
        self,
        level: str,
        category: str = "unknown",
        experiment_type: str = "unknown",
    ) -> None:
        """Record a detected anomaly.

        Args:
            level: Anomaly severity level.
            category: Anomaly category.
            experiment_type: Associated experiment type.
        """
        self.anomaly_count.labels(
            level=level, category=category, experiment_type=experiment_type
        ).inc()
        self.active_anomalies.labels(level=level).inc()

    def resolve_anomaly(self, level: str, resolution_seconds: float) -> None:
        """Record anomaly resolution.

        Args:
            level: Anomaly severity level.
            resolution_seconds: Time taken to resolve.
        """
        self.active_anomalies.labels(level=level).dec()
        self.anomaly_resolution_seconds.labels(level=level).observe(
            resolution_seconds
        )

    def update_equipment_utilization(
        self,
        equipment_type: str,
        equipment_id: str,
        utilization_percent: float,
    ) -> None:
        """Update equipment utilization gauge.

        Args:
            equipment_type: Type of equipment.
            equipment_id: Unique equipment identifier.
            utilization_percent: Current utilization (0-100).
        """
        self.equipment_utilization.labels(
            equipment_type=equipment_type, equipment_id=equipment_id
        ).set(utilization_percent)

    @contextmanager
    def inference_timer(
        self, model_name: str
    ) -> Generator[None, None, None]:
        """Context manager to time ML model inference.

        Args:
            model_name: Name of the ML model being used.

        Yields:
            None — timing is recorded on exit.

        Example:
            with metrics.inference_timer("anomaly_detector"):
                prediction = model.predict(data)
        """
        start = time.perf_counter()
        status = "success"
        try:
            yield
        except Exception:
            status = "error"
            raise
        finally:
            elapsed = time.perf_counter() - start
            self.model_inference_latency_seconds.labels(
                model_name=model_name
            ).observe(elapsed)
            self.model_inference_count.labels(
                model_name=model_name, status=status
            ).inc()

    @contextmanager
    def pipeline_stage_timer(
        self, stage: str
    ) -> Generator[None, None, None]:
        """Context manager to time a pipeline stage.

        Args:
            stage: Name of the pipeline stage.
        """
        start = time.perf_counter()
        try:
            yield
        except Exception as exc:
            self.pipeline_stage_errors.labels(
                stage=stage, error_type=type(exc).__name__
            ).inc()
            raise
        finally:
            elapsed = time.perf_counter() - start
            self.pipeline_stage_duration_seconds.labels(stage=stage).observe(elapsed)


# Module-level singleton
_metrics_instance: BRaaSMetrics | None = None


def get_metrics() -> BRaaSMetrics:
    """Get or create the global BRaaSMetrics singleton.

    Returns:
        The shared BRaaSMetrics instance.
    """
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = BRaaSMetrics()
    return _metrics_instance
