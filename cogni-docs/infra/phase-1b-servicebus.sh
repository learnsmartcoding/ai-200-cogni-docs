#!/bin/bash
# =============================================================================
# Phase 1c — Azure Service Bus: Namespace, Topic, Subscriptions, DLQ
# =============================================================================
# AI-200 Objectives:
#   ✅ Queue and process back-end operations using Azure Service Bus
#   ✅ Dead-letter queue (DLQ) handling
#   ✅ Messages, topics, and subscriptions
#
# KEY CONCEPTS:
#   Queue    = one sender, one receiver. Message is consumed once.
#   Topic    = one sender, MULTIPLE receivers. Each subscription gets its own copy.
#   DLQ      = Dead Letter Queue. Failed/expired messages land here automatically.
#
# WHY TOPIC (not Queue)?
#   We use a Topic so multiple workers can subscribe independently:
#     - embedding-worker: generates vector embeddings (Phase 2)
#     - notification-worker: could send email/Teams notification
#   Both receive the same message from the same upload event.
# =============================================================================

RESOURCE_GROUP="rg-cognidocs"
NAMESPACE="sb-cognidocs"
TOPIC="document-processing"

# ── Step 1: Create Service Bus Namespace ──────────────────────────────────────
# SKU Standard is REQUIRED for topics. Basic only supports queues.
# Standard costs ~$10/month base + very cheap per operation.
az servicebus namespace create \
  --name $NAMESPACE \
  --resource-group $RESOURCE_GROUP \
  --sku Standard

# ── Step 2: Create the Topic ──────────────────────────────────────────────────
# max-size-in-megabytes: total storage for this topic (1024 MB = 1 GB)
# default-message-time-to-live: messages auto-delete after 7 days if not consumed
az servicebus topic create \
  --name $TOPIC \
  --namespace-name $NAMESPACE \
  --resource-group $RESOURCE_GROUP \
  --max-size-in-megabytes 1024 \
  --default-message-time-to-live P7D

# ── Step 3: Create Subscription — embedding-worker ────────────────────────────
# This is the subscription our consumer.py reads from.
# dead-letter-on-message-expiration: automatically moves expired messages to DLQ
# max-delivery-count: after 3 failed deliveries, move to DLQ automatically
#   (this is what Azure does when your function keeps throwing exceptions)
az servicebus topic subscription create \
  --name "embedding-worker" \
  --topic-name $TOPIC \
  --namespace-name $NAMESPACE \
  --resource-group $RESOURCE_GROUP \
  --max-delivery-count 3 \
  --dead-letter-on-message-expiration true \
  --default-message-time-to-live P7D

# ── Step 4: (Optional) Create second subscription to demo fan-out ─────────────
# A second subscription independently receives the same messages.
# This demonstrates how topics enable multiple independent consumers.
az servicebus topic subscription create \
  --name "notification-worker" \
  --topic-name $TOPIC \
  --namespace-name $NAMESPACE \
  --resource-group $RESOURCE_GROUP \
  --max-delivery-count 3

# ── Step 5: Get the Connection String ─────────────────────────────────────────
# Copy this into your .env as AZURE_SERVICE_BUS_CONNECTION_STRING
# AND into Function App settings as AzureServiceBusConnectionString
echo "Service Bus connection string (for .env and Function App settings):"
az servicebus namespace authorization-rule keys list \
  --name RootManageSharedAccessKey \
  --namespace-name $NAMESPACE \
  --resource-group $RESOURCE_GROUP \
  --query primaryConnectionString \
  --output tsv

# ── Step 6: Add connection string to Function App settings ────────────────────
# Uncomment after copying the connection string above:
#
# SB_CONN=$(az servicebus namespace authorization-rule keys list \
#   --name RootManageSharedAccessKey \
#   --namespace-name $NAMESPACE \
#   --resource-group $RESOURCE_GROUP \
#   --query primaryConnectionString --output tsv)
#
# az functionapp config appsettings set \
#   --name func-cognidocs \
#   --resource-group $RESOURCE_GROUP \
#   --settings "AzureServiceBusConnectionString=$SB_CONN" \
#              "ServiceBusTopic=document-processing"

echo ""
echo "✅ Service Bus ready. Topics and subscriptions created."
echo "Next: add the connection string to .env and Function App settings."
