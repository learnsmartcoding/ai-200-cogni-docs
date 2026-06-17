# =============================================================================
# azure-login.ps1 — Authenticate Azure CLI on your local machine
# =============================================================================
# Run this ONCE before running any other infra script.
# You only need to re-run this if your session expires (usually after a few hours).
#
# HOW TO RUN:
#   Open PowerShell in VS Code terminal, then:
#   .\infra\azure-login.ps1
#
# WHAT IT DOES:
#   1. Opens a browser window to sign in to your Azure account
#   2. Sets the active subscription (if you have more than one)
#   3. Verifies login was successful
# =============================================================================

Write-Host "🔐 Logging in to Azure..." -ForegroundColor Cyan

# az login opens your browser for interactive sign-in.
# Once you sign in, the CLI stores a token locally — valid for several hours.
az login

# Show all subscriptions linked to your account
Write-Host "`n📋 Your Azure subscriptions:" -ForegroundColor Cyan
az account list --output table

# If you have multiple subscriptions, set the one you want to use.
# Replace the GUID below with your subscription ID from the table above.
# Skip this step if you only have one subscription.
#
# az account set --subscription "YOUR-SUBSCRIPTION-ID"

# Confirm which subscription is active
Write-Host "`n✅ Active subscription:" -ForegroundColor Green
az account show --query "{Name:name, SubscriptionId:id, State:state}" --output table
