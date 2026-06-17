# =============================================================================
# phase-1c-servicebus.ps1 — Azure Service Bus Setup
# =============================================================================
# AI-200 Objectives:
#   - Queue and process back-end operations using Azure Service Bus
#   - Dead-letter queue (DLQ) handling
#   - Messages, topics, and subscriptions
#
# PREREQUISITES:
#   Run .\infra\azure-login.ps1 first
#
# HOW TO RUN (from project root in VS Code terminal):
#   .\infra\phase-1c-servicebus.ps1
#
# KEY CONCEPT: Queue vs Topic
#   Queue = one sender, one receiver. Message consumed once.
#   Topic = one sender, MANY receivers. Each subscription gets its own copy.
#   We use a Topic so multiple workers independently receive the same event.
# =============================================================================

$RESOURCE_GROUP = "rg-cognidocs"
$NAMESPACE      = "sb-cognidocs"
$TOPIC          = "document-processing"

Write-Host ""
Write-Host "=== Phase 1c: Azure Service Bus Setup ===" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Create Service Bus Namespace ──────────────────────────────────────
# SKU Standard is REQUIRED for Topics. Basic tier only supports Queues.
Write-Host "[1/4] Creating Service Bus Namespace: $NAMESPACE ..." -ForegroundColor Yellow
az servicebus namespace create --name $NAMESPACE --resource-group $RESOURCE_GROUP --sku Standard --output table

# ── Step 2: Create Topic ──────────────────────────────────────────────────────
Write-Host ""
Write-Host "[2/4] Creating Topic: $TOPIC ..." -ForegroundColor Yellow
az servicebus topic create --name $TOPIC --namespace-name $NAMESPACE --resource-group $RESOURCE_GROUP --max-size-in-megabytes 1024 --default-message-time-to-live P7D --output table

# ── Step 3a: Create Subscription — embedding-worker ──────────────────────────
# max-delivery-count 3: after 3 failed deliveries, message moves to DLQ automatically
Write-Host ""
Write-Host "[3a/4] Creating Subscription: embedding-worker ..." -ForegroundColor Yellow
az servicebus topic subscription create --name "embedding-worker" --topic-name $TOPIC --namespace-name $NAMESPACE --resource-group $RESOURCE_GROUP --max-delivery-count 3 --enable-dead-lettering-on-message-expiration true --output table

# ── Step 3b: Create Subscription — notification-worker (fan-out demo) ─────────
# This subscription independently receives the same messages as embedding-worker.
# Demonstrates how Topics broadcast to multiple independent consumers.
Write-Host ""
Write-Host "[3b/4] Creating Subscription: notification-worker (fan-out demo) ..." -ForegroundColor Yellow
az servicebus topic subscription create --name "notification-worker" --topic-name $TOPIC --namespace-name $NAMESPACE --resource-group $RESOURCE_GROUP --max-delivery-count 3 --output table

# ── Step 4: Get and display the connection string ─────────────────────────────
Write-Host ""
Write-Host "[4/4] Retrieving connection string ..." -ForegroundColor Yellow
$SB_CONN = az servicebus namespace authorization-rule keys list --name RootManageSharedAccessKey --namespace-name $NAMESPACE --resource-group $RESOURCE_GROUP --query primaryConnectionString --output tsv

Write-Host ""
Write-Host "=== Done! Copy these into your .env file ===" -ForegroundColor Green
Write-Host ""
Write-Host "AZURE_SERVICE_BUS_CONNECTION_STRING=$SB_CONN"
Write-Host "AZURE_SERVICE_BUS_TOPIC=$TOPIC"
Write-Host "AZURE_SERVICE_BUS_SUBSCRIPTION=embedding-worker"
Write-Host ""
Write-Host "=== Also add to Function App settings (Phase 1b Step 4) ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "AzureServiceBusConnectionString=$SB_CONN"
Write-Host "ServiceBusTopic=$TOPIC"
