#!/usr/bin/env python3
"""Setup local DynamoDB table for development."""

import boto3
from botocore.exceptions import ClientError

# Local DynamoDB configuration
ENDPOINT_URL = "http://localhost:8000"
REGION = "us-east-1"
TABLE_NAME = "yomite-user-registration-local"

def create_table():
    """Create DynamoDB table with GSIs for local development."""
    dynamodb = boto3.client(
        'dynamodb',
        endpoint_url=ENDPOINT_URL,
        region_name=REGION,
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )
    
    try:
        # Check if table already exists
        dynamodb.describe_table(TableName=TABLE_NAME)
        print(f"Table '{TABLE_NAME}' already exists")
        return
    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceNotFoundException':
            raise
    
    # Create table
    print(f"Creating table '{TABLE_NAME}'...")
    
    dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {'AttributeName': 'PK', 'KeyType': 'HASH'},
            {'AttributeName': 'SK', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'PK', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'},
            {'AttributeName': 'Email', 'AttributeType': 'S'},
            {'AttributeName': 'EmailProviderKey', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'EmailIndex',
                'KeySchema': [
                    {'AttributeName': 'Email', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'EmailProviderIndex',
                'KeySchema': [
                    {'AttributeName': 'EmailProviderKey', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    print(f"Table '{TABLE_NAME}' created successfully!")
    print("\nTable details:")
    print(f"  - Endpoint: {ENDPOINT_URL}")
    print(f"  - Table Name: {TABLE_NAME}")
    print(f"  - Primary Key: PK (HASH), SK (RANGE)")
    print(f"  - GSI1: EmailIndex (Email, SK)")
    print(f"  - GSI2: EmailProviderIndex (EmailProviderKey, SK)")

if __name__ == '__main__':
    create_table()
