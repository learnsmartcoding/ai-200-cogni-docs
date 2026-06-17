#!/bin/bash
# =============================================================================
# Phase 1a — Azure Blob Storage Setup
# =============================================================================
# AI-200 Objective: Foundation for Event Grid (Phase 1b)
#
# Run these commands in Azure Cloud Shell (bash) or local Azure CLI.
# All resources go into the rg-cognidocs resource group.
#
# WHAT THIS CREATES:
#   - Resource Group:    rg-cognidocs
#   - Storage Account:   stcognidocs   (globally unique name — change if taken)
#   - Blob Container:    documents
# =============================================================================

# ── Variables — change these if names are already taken ───────────────────────
RESOURCE_GROUP="rg-cognidocs"
LOCATION="eastus"
STORAGE_ACCOUNT="stcognidocs"        # Must be globally unique, lowercase, no hyphens
CONTAINER_NAME="documents"

# ── Step 1: Create Resource Group ─────────────────────────────────────────────
# A resource group is a logical container for all related Azure resources.
# Deleting the resource group deletes everything inside it — useful for cleanup.
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# ── Step 2: Create Storage Account ────────────────────────────────────────────
# sku Standard_LRS = Locally Redundant Storage — cheapest option, fine for dev.
# kind StorageV2   = General Purpose v2, the recommended type for Blob Storage.
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2

# ── Step 3: Create Blob Container ─────────────────────────────────────────────
# public-access off = blobs are private (requires auth to access).
# Event Grid can still react to events from private containers.
az storage container create \
  --name $CONTAINER_NAME \
  --account-name $STORAGE_ACCOUNT \
  --public-access off

# ── Step 4: Get the Connection String ─────────────────────────────────────────
# Copy the output of this command and paste it into your .env file as:
# AZURE_STORAGE_CONNECTION_STRING=<output>
az storage account show-connection-string \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query connectionString \
  --output tsv

# ── Cleanup (run when done learning this phase) ───────────────────────────────
# Uncomment to delete all resources and stop all costs:
# az group delete --name $RESOURCE_GROUP --yes --no-wait
