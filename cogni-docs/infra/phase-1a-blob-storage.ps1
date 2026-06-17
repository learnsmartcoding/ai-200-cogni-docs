# =============================================================================
# phase-1a-blob-storage.ps1 — Azure Blob Storage Setup
# =============================================================================
# AI-200 Objective: Foundation for Event Grid (Phase 1b)
#
# PREREQUISITES:
#   1. Azure CLI installed: https://aka.ms/installazurecliwindows
#   2. Run .\infra\azure-login.ps1 first
#
# HOW TO RUN (from project root in VS Code terminal):
#   .\infra\phase-1a-blob-storage.ps1
#
# WHAT IT CREATES:
#   - Resource Group:  rg-cognidocs
#   - Storage Account: stcognidocs
#   - Blob Container:  documents
# =============================================================================

$RESOURCE_GROUP  = "rg-cognidocs"
$LOCATION        = "eastus"
$STORAGE_ACCOUNT = "stcognidocs"   # Must be globally unique, lowercase, no hyphens, 3-24 chars
$CONTAINER_NAME  = "documents"

Write-Host ""
Write-Host "=== Phase 1a: Azure Blob Storage Setup ===" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Create Resource Group ─────────────────────────────────────────────
# A resource group is a logical container for all related Azure resources.
# Deleting the resource group deletes everything inside it — useful for cleanup.
Write-Host "[1/4] Creating Resource Group: $RESOURCE_GROUP ..." -ForegroundColor Yellow
az group create --name $RESOURCE_GROUP --location $LOCATION --output table

# ── Step 2: Create Storage Account ────────────────────────────────────────────
# sku Standard_LRS = Locally Redundant Storage (cheapest, fine for dev/learning)
# kind StorageV2   = General Purpose v2, recommended for Blob Storage
Write-Host ""
Write-Host "[2/4] Creating Storage Account: $STORAGE_ACCOUNT ..." -ForegroundColor Yellow
az storage account create --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP --location $LOCATION --sku Standard_LRS --kind StorageV2 --output table

# ── Step 3: Create Blob Container ─────────────────────────────────────────────
# public-access off = blobs are private (auth required to access them directly)
# Event Grid can still react to events on private containers.
Write-Host ""
Write-Host "[3/4] Creating Blob Container: $CONTAINER_NAME ..." -ForegroundColor Yellow
az storage container create --name $CONTAINER_NAME --account-name $STORAGE_ACCOUNT --public-access off

# ── Step 4: Get and display the connection string ─────────────────────────────
Write-Host ""
Write-Host "[4/4] Retrieving connection string ..." -ForegroundColor Yellow
$CONN = az storage account show-connection-string --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP --query connectionString --output tsv

Write-Host ""
Write-Host "=== Done! Copy these into your .env file ===" -ForegroundColor Green
Write-Host ""
Write-Host "AZURE_STORAGE_CONNECTION_STRING=$CONN"
Write-Host "AZURE_STORAGE_CONTAINER=$CONTAINER_NAME"
