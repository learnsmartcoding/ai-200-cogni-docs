# =============================================================================
# initial-setup.ps1 -- One-time setup steps for AI-200 CogniDocs project
# =============================================================================
# Run individual sections as needed. Not meant to be run top-to-bottom.
# These are reference commands for things discovered during setup.
# =============================================================================


# -- Azure Provider Registration ----------------------------------------------
# Run these if az functionapp create or az eventgrid commands fail with
# "MissingSubscriptionRegistration" error.

az provider register --namespace Microsoft.Web

# Wait ~1-2 minutes, then run until it says "Registered":
az provider show --namespace Microsoft.Web --query "registrationState" --output tsv

# Once Registered, re-run the phase script:
# .\infra\phase-1b-function-eventgrid.ps1


az provider register --namespace Microsoft.EventGrid

# Wait ~1 minute, then check until it says "Registered":
az provider show --namespace Microsoft.EventGrid --query "registrationState" --output tsv


# -- Azure Functions Core Tools (func CLI) ------------------------------------
# Required for deploying Python Function Apps to Linux Consumption plan.
# az functionapp deployment source config-zip does NOT work reliably for
# Linux Python apps -- use "func azure functionapp publish" instead.
#
# Install option 1: npm (works on Windows if Node.js is installed)
npm install -g azure-functions-core-tools@4 --unsafe-perm true

# Install option 2: winget
# winget install Microsoft.AzureFunctionsCoreTools

# Install option 3: MSI download
# https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local?tabs=windows%2Cisolated-process%2Cnode-v4%2Cpython-v2%2Chttp-trigger%2Ccontainer-apps&pivots=programming-language-powershell

# Verify install (restart terminal first):
func --version


# -- Deploy Function App code to Azure ----------------------------------------
# Run from the project root. The --python flag is REQUIRED -- without it,
# func cannot detect the language and fails with "Worker runtime cannot be None".

cd worker
func azure functionapp publish func-cognidocs --python
cd ..
