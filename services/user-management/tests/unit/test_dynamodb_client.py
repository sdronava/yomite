"""Unit tests for DynamoDB client utility."""

import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from utils.dynamodb_client import DynamoDBClient  # noqa: E402


class TestDynamoDBClient:
    """Test DynamoDBClient class."""

    @pytest.fixture
    def mock_dynamodb(self):
        """Create mock DynamoDB resource."""
        with patch("utils.dynamodb_client.boto3.resource") as mock_resource:
            mock_table = MagicMock()
            mock_dynamodb = MagicMock()
            mock_dynamodb.Table.return_value = mock_table
            mock_resource.return_value = mock_dynamodb
            yield mock_table

    def test_dynamodb_client_initialization(self, mock_dynamodb):
        """Test DynamoDB client initialization."""
        client = DynamoDBClient(table_name="test-table")
        assert client.table_name == "test-table"

    def test_dynamodb_client_initialization_with_endpoint(self, mock_dynamodb):
        """Test DynamoDB client initialization with endpoint URL."""
        client = DynamoDBClient(table_name="test-table", endpoint_url="http://localhost:8000")
        assert client.table_name == "test-table"

    def test_put_item_success(self, mock_dynamodb):
        """Test successful put_item operation."""
        client = DynamoDBClient(table_name="test-table")
        item = {"PK": "USER#123", "SK": "PROFILE", "Name": "John"}

        client.put_item(item)

        mock_dynamodb.put_item.assert_called_once_with(Item=item)

    def test_put_item_with_retry_on_throttle(self, mock_dynamodb):
        """Test put_item retries on throttling."""
        client = DynamoDBClient(table_name="test-table")
        item = {"PK": "USER#123", "SK": "PROFILE"}

        # First call raises throttle error, second succeeds
        mock_dynamodb.put_item.side_effect = [
            ClientError(
                {"Error": {"Code": "ProvisionedThroughputExceededException"}},
                "PutItem",
            ),
            None,
        ]

        client.put_item(item, retry_count=2)

        assert mock_dynamodb.put_item.call_count == 2

    def test_get_item_success(self, mock_dynamodb):
        """Test successful get_item operation."""
        client = DynamoDBClient(table_name="test-table")
        expected_item = {"PK": "USER#123", "SK": "PROFILE", "Name": "John"}
        mock_dynamodb.get_item.return_value = {"Item": expected_item}

        result = client.get_item({"PK": "USER#123", "SK": "PROFILE"})

        assert result == expected_item

    def test_get_item_not_found(self, mock_dynamodb):
        """Test get_item when item not found."""
        client = DynamoDBClient(table_name="test-table")
        mock_dynamodb.get_item.return_value = {}

        result = client.get_item({"PK": "USER#123", "SK": "PROFILE"})

        assert result is None

    def test_get_item_with_retry_on_throttle(self, mock_dynamodb):
        """Test get_item retries on throttling."""
        client = DynamoDBClient(table_name="test-table")
        expected_item = {"PK": "USER#123", "SK": "PROFILE"}

        # First call raises throttle error, second succeeds
        mock_dynamodb.get_item.side_effect = [
            ClientError(
                {"Error": {"Code": "ProvisionedThroughputExceededException"}},
                "GetItem",
            ),
            {"Item": expected_item},
        ]

        result = client.get_item({"PK": "USER#123", "SK": "PROFILE"}, retry_count=2)

        assert result == expected_item
        assert mock_dynamodb.get_item.call_count == 2

    def test_query_success(self, mock_dynamodb):
        """Test successful query operation."""
        client = DynamoDBClient(table_name="test-table")
        expected_items = [
            {"PK": "USER#123", "SK": "PROFILE"},
            {"PK": "USER#123", "SK": "SESSION"},
        ]
        mock_dynamodb.query.return_value = {"Items": expected_items}

        result = client.query(
            "PK = :pk",
            {":pk": "USER#123"},
        )

        assert result == expected_items

    def test_query_with_index(self, mock_dynamodb):
        """Test query operation with GSI."""
        client = DynamoDBClient(table_name="test-table")
        expected_items = [{"PK": "USER#123", "SK": "PROFILE"}]
        mock_dynamodb.query.return_value = {"Items": expected_items}

        result = client.query(
            "Email = :email",
            {":email": "user@example.com"},
            index_name="EmailIndex",
        )

        assert result == expected_items
        call_kwargs = mock_dynamodb.query.call_args[1]
        assert call_kwargs["IndexName"] == "EmailIndex"

    def test_query_empty_result(self, mock_dynamodb):
        """Test query with no results."""
        client = DynamoDBClient(table_name="test-table")
        mock_dynamodb.query.return_value = {"Items": []}

        result = client.query("PK = :pk", {":pk": "USER#999"})

        assert result == []

    def test_update_item_success(self, mock_dynamodb):
        """Test successful update_item operation."""
        client = DynamoDBClient(table_name="test-table")
        updated_item = {"PK": "USER#123", "SK": "PROFILE", "Name": "Jane"}
        mock_dynamodb.update_item.return_value = {"Attributes": updated_item}

        result = client.update_item(
            "USER#123",
            "PROFILE",
            "SET #name = :name",
            {":name": "Jane"},
        )

        assert result == updated_item

    def test_update_item_with_attribute_names(self, mock_dynamodb):
        """Test update_item with expression attribute names."""
        client = DynamoDBClient(table_name="test-table")
        updated_item = {"PK": "USER#123", "SK": "PROFILE"}
        mock_dynamodb.update_item.return_value = {"Attributes": updated_item}

        result = client.update_item(
            "USER#123",
            "PROFILE",
            "SET #data.#name = :name",
            {":name": "Jane"},
            expression_attribute_names={"#data": "Data", "#name": "Name"},
        )

        assert result == updated_item
        call_kwargs = mock_dynamodb.update_item.call_args[1]
        assert call_kwargs["ExpressionAttributeNames"] == {
            "#data": "Data",
            "#name": "Name",
        }

    def test_delete_item_success(self, mock_dynamodb):
        """Test successful delete_item operation."""
        client = DynamoDBClient(table_name="test-table")

        client.delete_item("USER#123", "PROFILE")

        mock_dynamodb.delete_item.assert_called_once_with(
            Key={"PK": "USER#123", "SK": "PROFILE"}
        )

    def test_delete_item_with_retry_on_throttle(self, mock_dynamodb):
        """Test delete_item retries on throttling."""
        client = DynamoDBClient(table_name="test-table")

        # First call raises throttle error, second succeeds
        mock_dynamodb.delete_item.side_effect = [
            ClientError(
                {"Error": {"Code": "ProvisionedThroughputExceededException"}},
                "DeleteItem",
            ),
            None,
        ]

        client.delete_item("USER#123", "PROFILE", retry_count=2)

        assert mock_dynamodb.delete_item.call_count == 2
