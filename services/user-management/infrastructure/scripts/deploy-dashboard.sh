#!/bin/bash

# Deploy CloudWatch Dashboard for User Management Service
# Usage: ./deploy-dashboard.sh <environment>
# Example: ./deploy-dashboard.sh dev

set -e

ENVIRONMENT=${1:-dev}
DASHBOARD_NAME="yomite-user-management-${ENVIRONMENT}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_FILE="${SCRIPT_DIR}/../cloudwatch-dashboard.json"

echo "Deploying CloudWatch Dashboard: ${DASHBOARD_NAME}"
echo "Environment: ${ENVIRONMENT}"
echo "Dashboard file: ${DASHBOARD_FILE}"

# Check if dashboard file exists
if [ ! -f "${DASHBOARD_FILE}" ]; then
    echo "Error: Dashboard file not found: ${DASHBOARD_FILE}"
    exit 1
fi

# Replace environment placeholder in dashboard JSON
DASHBOARD_BODY=$(cat "${DASHBOARD_FILE}" | sed "s/\/dev/\/${ENVIRONMENT}/g")

# Deploy dashboard
aws cloudwatch put-dashboard \
    --dashboard-name "${DASHBOARD_NAME}" \
    --dashboard-body "${DASHBOARD_BODY}"

echo "✓ Dashboard deployed successfully!"
echo "View dashboard: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=${DASHBOARD_NAME}"
