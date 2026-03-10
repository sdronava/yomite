"""Monitoring utilities for CloudWatch metrics and X-Ray tracing."""

import os
import time
from typing import Any, Dict, Optional
from functools import wraps
import boto3
from aws_xray_sdk.core import xray_recorder, patch_all

# Patch AWS SDK and other libraries for X-Ray tracing
patch_all()

# Initialize CloudWatch client
cloudwatch = boto3.client("cloudwatch")

# Service name for metrics namespace
SERVICE_NAME = "UserManagement"
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")


def trace_function(name: Optional[str] = None):  # type: ignore[misc]
    """
    Decorator to add X-Ray tracing to a function.

    Args:
        name: Optional custom name for the subsegment

    Example:
        @trace_function("get_user_profile")
        def get_profile(user_id: str):
            # Function implementation
            pass
    """

    def decorator(func):  # type: ignore[no-untyped-def]
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            segment_name = name or func.__name__

            try:
                # Try to create subsegment for tracing
                subsegment = xray_recorder.begin_subsegment(segment_name)
                has_subsegment = subsegment is not None
            except Exception:
                # No X-Ray context (e.g., during testing)
                has_subsegment = False
                subsegment = None

            try:
                if has_subsegment and subsegment:
                    # Add metadata
                    subsegment.put_metadata("function", func.__name__)
                    subsegment.put_metadata("module", func.__module__)

                # Execute function
                result = func(*args, **kwargs)

                if has_subsegment and subsegment:
                    # Add result metadata (if not too large)
                    if result and isinstance(result, dict) and len(str(result)) < 1000:
                        subsegment.put_metadata("result_keys", list(result.keys()))

                return result

            except Exception as e:
                if has_subsegment and subsegment:
                    # Add error information
                    subsegment.put_annotation("error", True)
                    subsegment.put_metadata("error_type", type(e).__name__)
                    subsegment.put_metadata("error_message", str(e))
                raise

            finally:
                if has_subsegment:
                    try:
                        xray_recorder.end_subsegment()
                    except Exception:
                        pass

        return wrapper

    return decorator


def put_metric(
    metric_name: str,
    value: float,
    unit: str = "None",
    dimensions: Optional[Dict[str, str]] = None,
    namespace: Optional[str] = None,
):
    """
    Put a custom metric to CloudWatch.

    Args:
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement (Count, Seconds, Milliseconds, etc.)
        dimensions: Optional dimensions for the metric
        namespace: Optional custom namespace (defaults to SERVICE_NAME)

    Example:
        put_metric("ProfileRetrieved", 1, "Count", {"Environment": "prod"})
        put_metric("DynamoDBLatency", 0.123, "Seconds")
    """
    try:
        metric_namespace = namespace or f"{SERVICE_NAME}/{ENVIRONMENT}"

        # Build dimensions
        metric_dimensions = [{"Name": "Environment", "Value": ENVIRONMENT}]

        if dimensions:
            for key, value in dimensions.items():
                metric_dimensions.append({"Name": key, "Value": value})

        # Put metric
        cloudwatch.put_metric_data(
            Namespace=metric_namespace,
            MetricData=[
                {
                    "MetricName": metric_name,
                    "Value": value,
                    "Unit": unit,
                    "Dimensions": metric_dimensions,
                    "Timestamp": time.time(),
                }
            ],
        )

    except Exception as e:
        # Don't fail the request if metrics fail
        print(f"Failed to put metric {metric_name}: {e}")


def track_operation(operation_name: str, dimensions: Optional[Dict[str, str]] = None):  # type: ignore[misc]
    """
    Decorator to track operation metrics (count and duration).

    Args:
        operation_name: Name of the operation
        dimensions: Optional dimensions for the metrics

    Example:
        @track_operation("GetProfile", {"Operation": "Read"})
        def get_profile(user_id: str):
            # Function implementation
            pass
    """

    def decorator(func):  # type: ignore[no-untyped-def]
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()

            try:
                # Execute function
                result = func(*args, **kwargs)

                # Track success
                put_metric(f"{operation_name}Success", 1, "Count", dimensions)

                return result

            except Exception as e:
                # Track failure
                error_dimensions = dimensions.copy() if dimensions else {}
                error_dimensions["ErrorType"] = type(e).__name__

                put_metric(f"{operation_name}Error", 1, "Count", error_dimensions)

                raise

            finally:
                # Track duration
                duration = time.time() - start_time
                put_metric(f"{operation_name}Duration", duration, "Seconds", dimensions)

        return wrapper

    return decorator


def add_trace_annotation(key: str, value: Any):
    """
    Add an annotation to the current X-Ray segment.

    Annotations are indexed and can be used for filtering traces.

    Args:
        key: Annotation key
        value: Annotation value (string, number, or boolean)

    Example:
        add_trace_annotation("user_id", "user-123")
        add_trace_annotation("cache_hit", True)
    """
    try:
        segment = xray_recorder.current_segment()
        if segment:
            segment.put_annotation(key, value)
    except Exception:
        # Ignore if not in X-Ray context (e.g., during testing)
        pass


def add_trace_metadata(key: str, value: Any, namespace: str = "default"):
    """
    Add metadata to the current X-Ray segment.

    Metadata is not indexed but can contain more detailed information.

    Args:
        key: Metadata key
        value: Metadata value (any JSON-serializable object)
        namespace: Optional namespace for organizing metadata

    Example:
        add_trace_metadata("request_body", {"name": "John"})
        add_trace_metadata("db_query", "SELECT * FROM users", "database")
    """
    try:
        segment = xray_recorder.current_segment()
        if segment:
            segment.put_metadata(key, value, namespace)
    except Exception:
        # Ignore if not in X-Ray context (e.g., during testing)
        pass


class MetricsCollector:
    """
    Context manager for collecting multiple metrics.

    Example:
        with MetricsCollector("ProfileOperation") as metrics:
            # Do work
            metrics.add_metric("ItemsProcessed", 10, "Count")
            metrics.add_metric("CacheHitRate", 0.85, "Percent")
    """

    def __init__(self, operation_name: str, dimensions: Optional[Dict[str, str]] = None):
        self.operation_name = operation_name
        self.dimensions = dimensions or {}
        self.start_time: Optional[float] = None
        self.metrics: list[Dict[str, Any]] = []

    def __enter__(self) -> "MetricsCollector":
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        # Track duration
        duration = time.time() - self.start_time
        self.add_metric(f"{self.operation_name}Duration", duration, "Seconds")

        # Track success/failure
        if exc_type is None:
            self.add_metric(f"{self.operation_name}Success", 1, "Count")
        else:
            error_dimensions = self.dimensions.copy()
            error_dimensions["ErrorType"] = exc_type.__name__
            self.add_metric(f"{self.operation_name}Error", 1, "Count", error_dimensions)

        # Publish all metrics
        self._publish_metrics()

        # Don't suppress exceptions
        return False

    def add_metric(self, metric_name: str, value: float, unit: str = "None", 
                  dimensions: Optional[Dict[str, str]] = None):
        """Add a metric to be published when the context exits."""
        metric_dimensions = self.dimensions.copy()
        if dimensions:
            metric_dimensions.update(dimensions)

        self.metrics.append({"name": metric_name, "value": value, "unit": unit, "dimensions": metric_dimensions})

    def _publish_metrics(self) -> None:
        """Publish all collected metrics."""
        for metric in self.metrics:
            put_metric(metric["name"], metric["value"], metric["unit"], metric["dimensions"])


def track_dynamodb_operation(operation: str, table_name: str):  # type: ignore[misc]
    """
    Decorator to track DynamoDB operation metrics.

    Args:
        operation: DynamoDB operation (GetItem, PutItem, Query, etc.)
        table_name: DynamoDB table name

    Example:
        @track_dynamodb_operation("GetItem", "users-table")
        def get_user(user_id: str):
            # DynamoDB operation
            pass
    """

    def decorator(func):  # type: ignore[no-untyped-def]
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            dimensions = {"Operation": operation, "TableName": table_name}

            start_time = time.time()

            try:
                result = func(*args, **kwargs)

                # Track success
                put_metric("DynamoDBOperationSuccess", 1, "Count", dimensions)

                return result

            except Exception as e:
                # Track failure
                error_dimensions = dimensions.copy()
                error_dimensions["ErrorType"] = type(e).__name__

                put_metric("DynamoDBOperationError", 1, "Count", error_dimensions)

                raise

            finally:
                # Track latency
                latency = time.time() - start_time
                put_metric("DynamoDBOperationLatency", latency, "Seconds", dimensions)

        return wrapper

    return decorator


def track_cognito_authorization() -> None:
    """
    Track Cognito authorization metrics.

    Call this when a request is successfully authorized by Cognito.
    """
    put_metric("CognitoAuthorizationSuccess", 1, "Count")


def track_cognito_authorization_failure(reason: str = "Unknown") -> None:
    """
    Track Cognito authorization failure metrics.

    Args:
        reason: Reason for authorization failure
    """
    put_metric("CognitoAuthorizationFailure", 1, "Count", {"Reason": reason})
