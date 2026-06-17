#!/bin/bash
# =============================================================================
# Phase 1b — Azure Function App + Event Grid Setup
# =============================================================================
# AI-200 Objectives:
#   ✅ Build serverless APIs using Azure Functions (triggers and bindings)
#   ✅ Configure and deploy function apps
#   ✅ Implement event-driven workflows using Azure Event Grid
#
# Run in Azure Cloud Shell (bash) AFTER completing phase-1a-blob-storage.sh
# =============================================================================

RESOURCE_GROUP="rg-cognidocs"
LOCATION="eastus"
STORAGE_ACCOUNT="stcognidocs"
FUNCTION_APP="func-cognidocs"

# ── Step 1: Create the Function App ───────────────────────────────────────────
# IMPORTANT: Azure Functions supports Python 3.8, 3.9, 3.10, 3.11, 3.12 only.
# Even though you have Python 3.14 locally, set runtime-version to 3.12 in Azure.
# The code we write is compatible — only the Azure runtime version differs.
#
# --consumption-plan-location: use Consumption (serverless) plan — free tier.
#   You pay only per execution. At study volumes this costs ~$0.
# --os-type linux: required for Python functions.
az functionapp create \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --storage-account $STORAGE_ACCOUNT \
  --consumption-plan-location $LOCATION \
  --runtime python \
  --runtime-version 3.12 \
  --functions-version 4 \
  --os-type linux

# ── Step 2: Configure Application Settings ────────────────────────────────────
# These become environment variables inside the Function App.
# Our function_app.py reads these with os.environ.get(...)
# Add Service Bus connection string AFTER completing phase-1c-servicebus.sh
#
# az functionapp config appsettings set \
#   --name $FUNCTION_APP \
#   --resource-group $RESOURCE_GROUP \
#   --settings "AzureServiceBusConnectionString=<your-sb-connection-string>" \
#              "ServiceBusTopic=document-processing"

# ── Step 3: Deploy the function code ──────────────────────────────────────────
# We deploy using VS Code — see instructions below.
# Alternatively, use zip deploy via CLI:
#
# cd worker
# zip -r function.zip . -x "*.pyc" -x "__pycache__/*" -x "venv/*"
# az functionapp deployment source config-zip \
#   --name $FUNCTION_APP \
#   --resource-group $RESOURCE_GROUP \
#   --src function.zip

# ── Step 4: Get Function App URL (needed for Event Grid subscription) ──────────
echo "Function App URL:"
az functionapp show \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --query defaultHostName \
  --output tsv

# ── Step 5: Create Event Grid Subscription ────────────────────────────────────
# Event Grid will call our function when a blob is created in our container.
# NOTE: Deploy the function FIRST (Step 3) before creating this subscription,
#       because Azure validates the endpoint URL during creation.

STORAGE_RESOURCE_ID=$(az storage account show \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query id --output tsv)

# The endpoint URL for an Event Grid-triggered Azure Function follows this pattern:
# https://<function-app>.azurewebsites.net/runtime/webhooks/eventgrid
#       ?functionName=<function-name>&code=<host-key>
#
# Get the host key:
FUNCTION_KEY=$(az functionapp keys list \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --query systemKeys.eventgrid_extension \
  --output tsv)

FUNCTION_ENDPOINT="https://${FUNCTION_APP}.azurewebsites.net/runtime/webhooks/eventgrid?functionName=blob_created_handler&code=${FUNCTION_KEY}"

az eventgrid event-subscription create \
  --name "sub-cognidocs-blob-created" \
  --source-resource-id $STORAGE_RESOURCE_ID \
  --endpoint $FUNCTION_ENDPOINT \
  --endpoint-type webhook \
  --included-event-types "Microsoft.Storage.BlobCreated" \
  --subject-begins-with "/blobServices/default/containers/documents/blobs/raw/"
  # subject-begins-with: only fire for blobs in the raw/ prefix of our container.
  # Without this filter, Event Grid would fire for EVERY blob including internal ones.
  # This is the "filters" concept tested in AI-200.

echo "✅ Event Grid subscription created"
echo "Upload a file via the app and check:"
echo "   Azure Portal → Function App → Functions → blob_created_handler → Monitor"
