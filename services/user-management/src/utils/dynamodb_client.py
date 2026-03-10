"""DynamoDB client wrapper with retry logic and error handling."""

import os
import time
import logging
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError
import boto3

logger = logging.getLogger(__name__)


class DynamoDBClient:
    """Wrapper for DynamoDB operations with retry logic."""
    
    def __init__(self, table_name: Optional[str] = None, endpoint_url: Optional[str] = None):
        """
        Initialize DynamoDB client.
        
        Args:
            table_name: DynamoDB table name (defaults to env var)
            endpoint_url: DynamoDB endpoint URL (for local development)
        """
        self.table_name = table_name or os.getenv('DYNAMODB_TABLE_NAME')
        if not self.table_name:
            raise ValueError("DYNAMODB_TABLE_NAME must be set")
        
        # Use endpoint_url from parameter or environment variable
        endpoint = endpoint_url or os.getenv('DYNAMODB_ENDPOINT_URL')
        
        self.dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=endpoint,
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.table = self.dynamodb.Table(self.table_name)
        
        logger.info(f"DynamoDB client initialized for table: {self.table_name}")
    
    def put_item(self, item: Dict[str, Any], retry_count: int = 3) -> None:
        """
        Put item into DynamoDB with retry logic.
        
        Args:
            item: Item to put
            retry_count: Number of retries for throttling
            
        Raises:
            ClientError: If operation fails after retries
        """
        for attempt in range(retry_count):
            try:
                self.table.put_item(Item=item)
                logger.debug(f"Put item: PK={item.get('PK')}, SK={item.get('SK')}")
                return
            except ClientError as e:
                if e.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
                    if attempt < retry_count - 1:
                        wait_time = (2 ** attempt) * 0.1  # Exponential backoff
                        logger.warning(f"Throttled, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                logger.error(f"Failed to put item: {e}")
                raise
    
    def get_item(
        self, 
        key: Dict[str, str], 
        retry_count: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Get item from DynamoDB with retry logic.
        
        Args:
            key: Dictionary with PK and SK keys
            retry_count: Number of retries for throttling
            
        Returns:
            Item if found, None otherwise
            
        Raises:
            ClientError: If operation fails after retries
        """
        pk = key.get('PK')
        sk = key.get('SK')
        
        for attempt in range(retry_count):
            try:
                response = self.table.get_item(Key={'PK': pk, 'SK': sk})
                item = response.get('Item')
                logger.debug(f"Get item: PK={pk}, SK={sk}, Found={item is not None}")
                return item
            except ClientError as e:
                if e.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
                    if attempt < retry_count - 1:
                        wait_time = (2 ** attempt) * 0.1
                        logger.warning(f"Throttled, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                logger.error(f"Failed to get item: {e}")
                raise
        return None
    
    def query(
        self,
        key_condition_expression: str,
        expression_attribute_values: Dict[str, Any],
        index_name: Optional[str] = None,
        retry_count: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Query DynamoDB with retry logic.
        
        Args:
            key_condition_expression: Key condition expression
            expression_attribute_values: Expression attribute values
            index_name: GSI name (optional)
            retry_count: Number of retries for throttling
            
        Returns:
            List of items
            
        Raises:
            ClientError: If operation fails after retries
        """
        for attempt in range(retry_count):
            try:
                kwargs = {
                    'KeyConditionExpression': key_condition_expression,
                    'ExpressionAttributeValues': expression_attribute_values
                }
                if index_name:
                    kwargs['IndexName'] = index_name
                
                response = self.table.query(**kwargs)
                items = response.get('Items', [])
                logger.debug(
                    f"Query: Index={index_name}, Count={len(items)}"
                )
                return items
            except ClientError as e:
                if e.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
                    if attempt < retry_count - 1:
                        wait_time = (2 ** attempt) * 0.1
                        logger.warning(f"Throttled, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                logger.error(f"Failed to query: {e}")
                raise
        return []
    
    def update_item(
        self,
        pk: str,
        sk: str,
        update_expression: str,
        expression_attribute_values: Dict[str, Any],
        expression_attribute_names: Optional[Dict[str, str]] = None,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """
        Update item in DynamoDB with retry logic.
        
        Args:
            pk: Partition key value
            sk: Sort key value
            update_expression: Update expression
            expression_attribute_values: Expression attribute values
            expression_attribute_names: Expression attribute names (optional)
            retry_count: Number of retries for throttling
            
        Returns:
            Updated item attributes
            
        Raises:
            ClientError: If operation fails after retries
        """
        for attempt in range(retry_count):
            try:
                kwargs = {
                    'Key': {'PK': pk, 'SK': sk},
                    'UpdateExpression': update_expression,
                    'ExpressionAttributeValues': expression_attribute_values,
                    'ReturnValues': 'ALL_NEW'
                }
                if expression_attribute_names:
                    kwargs['ExpressionAttributeNames'] = expression_attribute_names
                
                response = self.table.update_item(**kwargs)
                logger.debug(f"Update item: PK={pk}, SK={sk}")
                return response.get('Attributes', {})
            except ClientError as e:
                if e.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
                    if attempt < retry_count - 1:
                        wait_time = (2 ** attempt) * 0.1
                        logger.warning(f"Throttled, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                logger.error(f"Failed to update item: {e}")
                raise
        return {}
    
    def delete_item(self, pk: str, sk: str, retry_count: int = 3) -> None:
        """
        Delete item from DynamoDB with retry logic.
        
        Args:
            pk: Partition key value
            sk: Sort key value
            retry_count: Number of retries for throttling
            
        Raises:
            ClientError: If operation fails after retries
        """
        for attempt in range(retry_count):
            try:
                self.table.delete_item(Key={'PK': pk, 'SK': sk})
                logger.debug(f"Delete item: PK={pk}, SK={sk}")
                return
            except ClientError as e:
                if e.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
                    if attempt < retry_count - 1:
                        wait_time = (2 ** attempt) * 0.1
                        logger.warning(f"Throttled, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                logger.error(f"Failed to delete item: {e}")
                raise
