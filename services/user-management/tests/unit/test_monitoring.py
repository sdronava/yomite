"""
Unit tests for monitoring utilities.

Tests cover CloudWatch metrics, X-Ray tracing decorators, and error handling paths.
"""

import sys
import os
import time
from unittest.mock import MagicMock, Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from utils.monitoring import (  # noqa: E402
    MetricsCollector,
    add_trace_annotation,
    add_trace_metadata,
    put_metric,
    trace_function,
    track_cognito_authorization,
    track_cognito_authorization_failure,
    track_dynamodb_operation,
    track_operation,
)


class TestTraceFunction:
    """Tests for trace_function decorator."""

    @patch("utils.monitoring.xray_recorder")
    def test_trace_function_without_xray_context(self, mock_xray):
        """Test trace_function decorator when X-Ray context is unavailable."""
        # Simulate X-Ray context unavailable
        mock_xray.begin_subsegment.side_effect = Exception("No X-Ray context")

        @trace_function("test_operation")
        def sample_function():
            return "success"

        # Should not raise exception, should handle gracefully
        result = sample_function()
        assert result == "success"

    @patch("utils.monitoring.xray_recorder")
    def test_trace_function_with_exception_in_function(self, mock_xray):
        """Test trace_function decorator when decorated function raises exception."""
        mock_subsegment = MagicMock()
        mock_xray.begin_subsegment.return_value = mock_subsegment

        @trace_function("test_operation")
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function()

        # Verify error metadata was added
        mock_subsegment.put_annotation.assert_called_with("error", True)
        assert mock_subsegment.put_metadata.call_count >= 2  # error_type and error_message

    @patch("utils.monitoring.xray_recorder")
    def test_trace_function_end_subsegment_fails(self, mock_xray):
        """Test trace_function decorator when ending subsegment fails."""
        mock_subsegment = MagicMock()
        mock_xray.begin_subsegment.return_value = mock_subsegment
        mock_xray.end_subsegment.side_effect = Exception("Failed to end subsegment")

        @trace_function("test_operation")
        def sample_function():
            return "success"

        # Should not raise exception, should handle gracefully
        result = sample_function()
        assert result == "success"


class TestPutMetric:
    """Tests for put_metric function."""

    @patch("utils.monitoring.cloudwatch")
    def test_put_metric_with_cloudwatch_failure(self, mock_cloudwatch):
        """Test put_metric when CloudWatch call fails."""
        mock_cloudwatch.put_metric_data.side_effect = Exception("CloudWatch unavailable")

        # Should not raise exception, should handle gracefully
        put_metric("TestMetric", 1.0, "Count")

        # Verify CloudWatch was called
        mock_cloudwatch.put_metric_data.assert_called_once()

    @patch("utils.monitoring.cloudwatch")
    def test_put_metric_with_custom_namespace(self, mock_cloudwatch):
        """Test put_metric with custom namespace."""
        put_metric("TestMetric", 1.0, "Count", namespace="CustomNamespace")

        # Verify namespace was used
        call_args = mock_cloudwatch.put_metric_data.call_args
        assert call_args[1]["Namespace"] == "CustomNamespace"


class TestTrackOperation:
    """Tests for track_operation decorator."""

    @patch("utils.monitoring.put_metric")
    def test_track_operation_with_exception(self, mock_put_metric):
        """Test track_operation decorator when decorated function raises exception."""

        @track_operation("TestOperation", {"Service": "Test"})
        def failing_function():
            raise RuntimeError("Test error")

        with pytest.raises(RuntimeError, match="Test error"):
            failing_function()

        # Verify error metric was published
        error_calls = [call for call in mock_put_metric.call_args_list if "Error" in str(call)]
        assert len(error_calls) > 0

        # Verify duration metric was still published (in finally block)
        duration_calls = [call for call in mock_put_metric.call_args_list if "Duration" in str(call)]
        assert len(duration_calls) > 0


class TestAddTraceAnnotation:
    """Tests for add_trace_annotation function."""

    @patch("utils.monitoring.xray_recorder")
    def test_add_trace_annotation_without_xray_context(self, mock_xray):
        """Test add_trace_annotation when X-Ray context is unavailable."""
        mock_xray.current_segment.side_effect = Exception("No X-Ray context")

        # Should not raise exception, should handle gracefully
        add_trace_annotation("test_key", "test_value")

    @patch("utils.monitoring.xray_recorder")
    def test_add_trace_annotation_with_none_segment(self, mock_xray):
        """Test add_trace_annotation when current segment is None."""
        mock_xray.current_segment.return_value = None

        # Should not raise exception, should handle gracefully
        add_trace_annotation("test_key", "test_value")


class TestAddTraceMetadata:
    """Tests for add_trace_metadata function."""

    @patch("utils.monitoring.xray_recorder")
    def test_add_trace_metadata_without_xray_context(self, mock_xray):
        """Test add_trace_metadata when X-Ray context is unavailable."""
        mock_xray.current_segment.side_effect = Exception("No X-Ray context")

        # Should not raise exception, should handle gracefully
        add_trace_metadata("test_key", {"data": "value"})

    @patch("utils.monitoring.xray_recorder")
    def test_add_trace_metadata_with_none_segment(self, mock_xray):
        """Test add_trace_metadata when current segment is None."""
        mock_xray.current_segment.return_value = None

        # Should not raise exception, should handle gracefully
        add_trace_metadata("test_key", {"data": "value"}, "custom_namespace")


class TestMetricsCollector:
    """Tests for MetricsCollector context manager."""

    @patch("utils.monitoring.put_metric")
    def test_metrics_collector_with_exception(self, mock_put_metric):
        """Test MetricsCollector when exception occurs in context."""
        try:
            with MetricsCollector("TestOperation", {"Service": "Test"}) as metrics:
                metrics.add_metric("CustomMetric", 5.0, "Count")
                raise ValueError("Test error")
        except ValueError:
            pass

        # Verify error metric was published
        error_calls = [call for call in mock_put_metric.call_args_list if "Error" in str(call)]
        assert len(error_calls) > 0

        # Verify custom metric was still published
        custom_calls = [call for call in mock_put_metric.call_args_list if "CustomMetric" in str(call)]
        assert len(custom_calls) > 0

    @patch("utils.monitoring.put_metric")
    def test_metrics_collector_success_path(self, mock_put_metric):
        """Test MetricsCollector on successful execution."""
        with MetricsCollector("TestOperation") as metrics:
            metrics.add_metric("ItemsProcessed", 10.0, "Count")

        # Verify success metric was published
        success_calls = [call for call in mock_put_metric.call_args_list if "Success" in str(call)]
        assert len(success_calls) > 0

        # Verify duration metric was published
        duration_calls = [call for call in mock_put_metric.call_args_list if "Duration" in str(call)]
        assert len(duration_calls) > 0


class TestTrackDynamoDBOperation:
    """Tests for track_dynamodb_operation decorator."""

    @patch("utils.monitoring.put_metric")
    def test_track_dynamodb_operation_with_exception(self, mock_put_metric):
        """Test track_dynamodb_operation decorator when operation fails."""

        @track_dynamodb_operation("GetItem", "users-table")
        def failing_operation():
            raise Exception("DynamoDB error")

        with pytest.raises(Exception, match="DynamoDB error"):
            failing_operation()

        # Verify error metric was published
        error_calls = [call for call in mock_put_metric.call_args_list if "Error" in str(call)]
        assert len(error_calls) > 0

        # Verify latency metric was still published (in finally block)
        latency_calls = [call for call in mock_put_metric.call_args_list if "Latency" in str(call)]
        assert len(latency_calls) > 0


class TestCognitoTracking:
    """Tests for Cognito authorization tracking functions."""

    @patch("utils.monitoring.put_metric")
    def test_track_cognito_authorization(self, mock_put_metric):
        """Test track_cognito_authorization function."""
        track_cognito_authorization()

        # Verify metric was published
        mock_put_metric.assert_called_once_with("CognitoAuthorizationSuccess", 1, "Count")

    @patch("utils.monitoring.put_metric")
    def test_track_cognito_authorization_failure(self, mock_put_metric):
        """Test track_cognito_authorization_failure function."""
        track_cognito_authorization_failure("InvalidToken")

        # Verify metric was published with reason
        mock_put_metric.assert_called_once_with("CognitoAuthorizationFailure", 1, "Count", {"Reason": "InvalidToken"})
