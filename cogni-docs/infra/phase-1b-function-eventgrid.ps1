# =============================================================================
# phase-1b-function-eventgrid.ps1 -- Azure Function App + Event Grid Setup
# =============================================================================
# AI-200 Objectives:
#   - Build serverless APIs using Azure Functions (triggers and bindings)
#   - Configure and deploy function apps
#   - Implement event-driven workflows using Azure Event Grid
#
# PREREQUISITES -- RUN IN THIS ORDER:
#   1. .\infra\azure-login.ps1            (authenticate)
#   2. .\infra\phase-1a-blob-storage.ps1  (Storage Account must exist)
#   3. .\infra\phase-1c-servicebus.ps1    (Service Bus must exist BEFORE this script)
#      Copy AZURE_SERVICE_BUS_CONNECTION_STRING output into your .env file
#   4. .\infra\phase-1b-function-eventgrid.ps1   <-- YOU ARE HERE
#
# WARNING: The script naming (1a, 1b, 1c) maps to VIDEO numbers, NOT run order.
#          Run order is always: 1a -> 1c -> 1b
#          Running 1b before 1c means the Function App gets an empty/invalid
#          Service Bus connection string -> Function fires but fails with
#          AMQPConnectionError "Name or service not known"
#
# HOW TO RUN (from project root in VS Code terminal):
#   .\infra\phase-1b-function-eventgrid.ps1
#
# NOTE on Step 4 (Event Grid subscription):
#   The CLI command for Event Grid fails on cold-start Consumption plan apps
#   because Azure tries to do a webhook validation handshake, but the Function
#   App hasn't warmed up yet. Step 4 must be done via the Azure Portal instead.
#   Instructions are printed at the end of this script.
# =============================================================================

$RESOURCE_GROUP  = "rg-cognidocs"
$LOCATION        = "eastus"
$STORAGE_ACCOUNT = "stcognidocs"
$FUNCTION_APP    = "func-cognidocs"
$TOPIC           = "document-processing"
$CONTAINER_NAME  = "documents"

Write-Host ""
Write-Host "=== Phase 1b: Azure Function App + Event Grid Setup ===" -ForegroundColor Cyan
Write-Host ""

# -- Step 1: Create the Function App ------------------------------------------
# IMPORTANT: Azure Functions supports Python 3.8-3.12 only.
# Even though you have Python 3.14 locally, we deploy with runtime-version 3.12.
# The code is compatible -- only the Azure runtime version differs.
# Consumption plan = serverless, pay per execution (~free at study volumes).
# os-type linux is required for Python function apps.
Write-Host "[1/3] Creating Function App: $FUNCTION_APP ..." -ForegroundColor Yellow
Write-Host "      Note: Using Python 3.12 runtime (Azure does not support 3.14 yet)" -ForegroundColor Gray
Write-Host "      Note: If the app already exists, this command updates it gracefully." -ForegroundColor Gray
az functionapp create --name $FUNCTION_APP --resource-group $RESOURCE_GROUP --storage-account $STORAGE_ACCOUNT --consumption-plan-location $LOCATION --runtime python --runtime-version 3.12 --functions-version 4 --os-type linux --output table
Write-Host "      Function App ready." -ForegroundColor Green

# -- Step 2: Configure Application Settings -----------------------------------
# These become os.environ variables inside the running Function.
# Our function_app.py reads them with: os.environ.get("AzureServiceBusConnectionString")
#
# CRITICAL: AzureWebJobsFeatureFlags=EnableWorkerIndexing
#   This flag is REQUIRED for the Python v2 programming model (decorator-based).
#   Without it, the Functions runtime uses the old v1 model and cannot discover
#   functions defined with @app.event_grid_trigger(...) decorators.
#   The portal will show "No functions found" in the Functions tab without this.
#   (Python equivalent of enabling a feature flag in .NET appsettings.json)
Write-Host ""
Write-Host "[2/3] Configuring Application Settings ..." -ForegroundColor Yellow

# Read Service Bus connection string from your local .env file.
# Real secrets must be in .env (not .env.example -- that file is committed to Git).
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found in project root." -ForegroundColor Red
    Write-Host "       Copy .env.example to .env and fill in your real values." -ForegroundColor Red
    exit 1
}
$envLine = Get-Content ".env" | Where-Object { $_ -match "^AZURE_SERVICE_BUS_CONNECTION_STRING=.+" }
if (-not $envLine) {
    Write-Host "ERROR: AZURE_SERVICE_BUS_CONNECTION_STRING not found or empty in .env" -ForegroundColor Red
    Write-Host "       Run phase-1c-servicebus.ps1, copy the output into .env (not .env.example)." -ForegroundColor Red
    Write-Host "       .env file location: $(Resolve-Path '.env')" -ForegroundColor Gray
    exit 1
}
$SB_CONN = ($envLine -split "=", 2)[1]

az functionapp config appsettings set --name $FUNCTION_APP --resource-group $RESOURCE_GROUP --settings "AzureServiceBusConnectionString=$SB_CONN" "ServiceBusTopic=$TOPIC" "AzureWebJobsFeatureFlags=EnableWorkerIndexing" --output table
Write-Host "      App settings configured (EnableWorkerIndexing added for Python v2 model)." -ForegroundColor Green

# -- Step 3: Deploy the Function code -----------------------------------------
# Uses Azure Functions Core Tools (func CLI) to deploy from the worker/ folder.
#
# WHY NOT az functionapp deployment source config-zip?
#   That command returns "Bad Request" for Linux Python Consumption plan apps.
#   It sends a raw zip to Kudu which does NOT run pip install -- so packages
#   from requirements.txt are never installed and the Python worker fails to start.
#   No pip install = no azure-servicebus = no functions discovered in portal.
#
# func azure functionapp publish --python:
#   Uses the correct Linux deployment endpoint, triggers a remote build on Azure,
#   and runs pip install -r requirements.txt server-side before starting the app.
#
# PREREQUISITE: func CLI must be installed.
#   npm install -g azure-functions-core-tools@4 --unsafe-perm true
#   See infra\initial-setup.ps1 for details.
#
# IMPORTANT: host.json must be pure valid JSON -- no // comments allowed.
#   The Functions runtime parses host.json on startup. Any syntax error
#   prevents the runtime from loading and NO functions appear in the portal.
Write-Host ""
Write-Host "[3/3] Deploying Function code from worker/ folder ..." -ForegroundColor Yellow
Write-Host "      Using func CLI (not az zip deploy -- see comment above for why)" -ForegroundColor Gray

# Push-Location / Pop-Location = PowerShell equivalent of cd + cd back
# func publish must run FROM the worker/ directory
Push-Location "worker"
func azure functionapp publish $FUNCTION_APP --python
Pop-Location

Write-Host "      Function code deployed." -ForegroundColor Green
Write-Host "      Expected output above: 'Remote build succeeded!' + 'blob_created_handler'" -ForegroundColor Gray

# -- Step 4 (MANUAL - Portal only): Create Event Grid Subscription ------------
# WHY NOT CLI: The CLI creates a Webhook-type subscription and Azure immediately
# sends a validation handshake to the Function URL. On a Consumption plan, the
# app is cold and the handshake times out, so subscription creation fails.
# The Azure Portal uses "Azure Function" endpoint type which skips the handshake.
#
# PORTAL STEPS (do this after running this script):
#   1. Go to: portal.azure.com -> Storage Accounts -> stcognidocs -> Events
#   2. Click "+ Event Subscription"
#   3. SYSTEM TOPIC (first-time only):
#        The portal asks you to create a System Topic before the subscription.
#        A System Topic is an Azure resource that represents the event source
#        (the storage account). Azure needs one to route events from storage.
#        Name: evgt-cognidocs-storage
#        You only create this once -- future subscriptions reuse it.
#   4. Fill in the subscription details:
#        Name:              sub-cognidocs-blob-created
#        Event Schema:      Event Grid Schema
#        Filter to Event:   [x] Blob Created  (uncheck all others)
#   5. Endpoint Type:       Azure Function   <-- use this, NOT Webhook
#   6. Endpoint:            Click "Select endpoint"
#                           Resource Group:  rg-cognidocs
#                           Function App:    func-cognidocs
#                           Function:        blob_created_handler
#   7. Click "Filters" tab:
#        Enable subject filtering: checked
#        Subject Begins With:  /blobServices/default/containers/documents/blobs/raw/
#   8. Click "Create"

Write-Host ""
Write-Host "=== Steps 1-3 complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "NEXT: Create the Event Grid subscription manually in the Azure Portal." -ForegroundColor Cyan
Write-Host "      (CLI creation fails on cold-start Consumption plan - portal bypasses this)" -ForegroundColor Gray
Write-Host ""
Write-Host "  Portal steps:" -ForegroundColor White
Write-Host "  1. portal.azure.com -> Storage Accounts -> stcognidocs -> Events" -ForegroundColor White
Write-Host "  2. Click '+ Event Subscription'" -ForegroundColor White
Write-Host "  3. SYSTEM TOPIC (first-time only): Name it evgt-cognidocs-storage" -ForegroundColor Yellow
Write-Host "     (Azure creates this once to represent the storage account as an event source)" -ForegroundColor Gray
Write-Host "  4. Name: sub-cognidocs-blob-created" -ForegroundColor White
Write-Host "  5. Event Type: Blob Created only" -ForegroundColor White
Write-Host "  6. Endpoint Type: Azure Function (NOT Webhook)" -ForegroundColor White
Write-Host "  7. Function: func-cognidocs -> blob_created_handler" -ForegroundColor White
Write-Host "  8. Filters tab -> Subject Begins With: /blobServices/default/containers/$CONTAINER_NAME/blobs/raw/" -ForegroundColor White
Write-Host ""
Write-Host "  Verify the function now appears in:" -ForegroundColor White
Write-Host "  portal.azure.com -> Function Apps -> func-cognidocs -> Functions" -ForegroundColor White
Write-Host ""
Write-Host "  Then test: Upload a file via Streamlit and check:" -ForegroundColor White
Write-Host "  Function Apps -> func-cognidocs -> Functions -> blob_created_handler -> Monitor" -ForegroundColor White
