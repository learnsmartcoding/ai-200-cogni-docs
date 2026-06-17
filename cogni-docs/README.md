# CogniDocs
### Intelligent Document Processing & Semantic Search Platform

> **AI-200 Certification Study Project**
> Built phase by phase, covering every objective of the Microsoft AI-200 exam.
> Each phase = one or more exam objectives = one or more YouTube videos.

---

## Prerequisites

Everything below needs to be installed on your Windows machine before starting.
Items marked **Phase 0** are needed from the very first video. Items marked **Phase 1+** can be installed when you reach that phase.

---

### Software to Install

#### Python — Phase 0
Download: https://www.python.org/downloads/

| | |
|---|---|
| **Version** | 3.12 or higher (tested on 3.14.2) |
| **Installer** | Windows installer (64-bit) |
| **During install** | Check "Add Python to PATH" ✅ |
| **Verify** | `python --version` |

> **Windows note:** Always prefix commands with `python -m` in PowerShell:
> `python -m pip install`, `python -m uvicorn main:app`, `python -m streamlit run app.py`
> Bare `pip`, `uvicorn`, `streamlit` are often not on PATH even with venv active.

---

#### Git — Phase 0
Download: https://git-scm.com/download/win

| | |
|---|---|
| **Version** | Latest |
| **During install** | All defaults are fine |
| **Verify** | `git --version` |

---

#### Docker Desktop — Phase 0
Download: https://www.docker.com/products/docker-desktop/

| | |
|---|---|
| **Version** | Latest |
| **Purpose** | Runs PostgreSQL 16 + Redis 7 locally (no Azure cost for local dev) |
| **Verify** | `docker --version` and `docker compose version` |
| **Note** | Must be running (system tray icon) before `docker compose up -d` |

---

#### Visual Studio Code — Phase 0
Download: https://code.visualstudio.com/

| | |
|---|---|
| **Version** | Latest |
| **Verify** | `code --version` |
| **Important** | Always open VS Code at the **project root** (`C:\Work\AI-200\cogni-docs`), not a subfolder. The root is where `.git`, `docker-compose.yml`, and `README.md` live. Opening a subfolder means git changes won't show in Source Control. |

---

#### Azure CLI — Phase 1
Download: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows

| | |
|---|---|
| **Version** | Latest (MSI installer recommended on Windows) |
| **Purpose** | Create Azure resources from PowerShell terminal |
| **Verify** | `az --version` |
| **First use** | Run `.\infra\azure-login.ps1` to authenticate |

---

#### Node.js — Phase 1
Download: https://nodejs.org/ (LTS version)

| | |
|---|---|
| **Version** | LTS (18.x or 20.x) |
| **Purpose** | Required to install Azure Functions Core Tools via npm |
| **Verify** | `node --version` and `npm --version` |

---

#### Azure Functions Core Tools v4 — Phase 1
Install via npm after Node.js is installed:

```powershell
npm install -g azure-functions-core-tools@4 --unsafe-perm true
```

| | |
|---|---|
| **Version** | v4 (matches Azure Functions runtime version 4) |
| **Purpose** | Deploy Python function apps to Azure (required -- `az` zip deploy does not work for Linux Python) |
| **Verify** | `func --version` (should show 4.x.x) |
| **Note** | Restart terminal after install for `func` to be on PATH |

> **Why `--unsafe-perm true`?** On Windows, npm sometimes fails to install global packages with
> the default permissions. This flag bypasses that restriction safely for CLI tools.

---

### VS Code Extensions

Install from the Extensions panel (`Ctrl+Shift+X`) or click the links below.

#### Phase 0 — Required from the start

| Extension | Publisher | ID | Purpose |
|---|---|---|---|
| **Python** | Microsoft | `ms-python.python` | IntelliSense, linting, venv selection, debugger |
| **Pylance** | Microsoft | `ms-python.vscode-pylance` | Fast type checking and autocomplete for Python |
| **Docker** | Microsoft | `ms-azuretools.vscode-docker` | View containers, images, compose files with GUI |
| **REST Client** | Huachao Mao | `humao.rest-client` | Test API endpoints directly from `.http` files (replaces Postman) |

#### Phase 1+ — Install when you reach Azure work

| Extension | Publisher | ID | Purpose |
|---|---|---|---|
| **Azure Functions** | Microsoft | `ms-azuretools.vscode-azurefunctions` | Deploy functions, view logs, manage function apps from VS Code |
| **Azure Resources** | Microsoft | `ms-azuretools.vscode-azureresourcegroups` | Browse all Azure resources in a sidebar tree |
| **Azure Storage** | Microsoft | `ms-azuretools.vscode-azurestorage` | Browse blob containers, upload/download files from VS Code |
| **Azure Databases** | Microsoft | `ms-azuretools.vscode-cosmosdb` | Connect to PostgreSQL, Cosmos DB, view tables and documents |
| **Azure Service Bus Explorer** | Piotr Rogala | `piotr-rogala.azure-sb-explorer` | Browse Service Bus topics, subscriptions, peek messages |

#### Optional but recommended

| Extension | Publisher | ID | Purpose |
|---|---|---|---|
| **GitLens** | GitKraken | `eamodio.gitlens` | Inline git blame, history, branch comparison |
| **indent-rainbow** | oderwat | `oderwat.indent-rainbow` | Coloured indentation guides — great for Python |
| **Thunder Client** | Ranga Vadhineni | `rangav.vscode-thunder-client` | Lightweight Postman alternative built into VS Code |

---

### One-Time PowerShell Setup

Run once to allow local `.ps1` scripts to execute:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Verify:
```powershell
Get-ExecutionPolicy -Scope CurrentUser
# Should output: RemoteSigned
```

---

### Quick Install Checklist

```
[ ] Python 3.12+          python --version
[ ] Git                   git --version
[ ] Docker Desktop        docker --version  (and Docker running in system tray)
[ ] VS Code               code --version
[ ] Azure CLI             az --version          (Phase 1)
[ ] Node.js               node --version         (Phase 1)
[ ] func CLI v4           func --version         (Phase 1)
[ ] PowerShell policy     Get-ExecutionPolicy -Scope CurrentUser  -> RemoteSigned

VS Code Extensions:
[ ] ms-python.python
[ ] ms-python.vscode-pylance
[ ] ms-azuretools.vscode-docker
[ ] humao.rest-client
[ ] ms-azuretools.vscode-azurefunctions         (Phase 1)
[ ] ms-azuretools.vscode-azureresourcegroups    (Phase 1)
[ ] ms-azuretools.vscode-azurestorage           (Phase 1)
[ ] ms-azuretools.vscode-cosmosdb               (Phase 1)
```

> **VS Code note:** Always open VS Code at the **project root** (`C:\Work\AI-200\cogni-docs`), not a subfolder. The root is where `.git`, `docker-compose.yml`, and `README.md` live.

---

## Running Azure Setup Scripts

Each phase has infrastructure that needs to be created in Azure before the code will work.
There are **three ways** to do this — choose what works best for you.

---

### Option 1 — Azure Portal (GUI) 🖱️
**Best for:** First-time learners, visual understanding, seeing every setting

Go to [portal.azure.com](https://portal.azure.com) and create each resource manually through the UI.
Use the `.sh` or `.ps1` scripts as a **reference checklist** — they list every setting you need to fill in.

**Pros:** Visual, beginner-friendly, great for understanding what each setting does
**Cons:** Not repeatable — you have to click everything again for each demo

---

### Option 2 — Azure Cloud Shell (bash in browser) 🌐
**Best for:** Running `.sh` scripts without any local install

1. Go to [shell.azure.com](https://shell.azure.com) (or click the `>_` icon in the Azure portal header)
2. Choose **Bash**
3. Upload or paste the `.sh` script contents and run them

The `.sh` files in `infra/` run as-is in Cloud Shell — no conversion needed.

```bash
# In Azure Cloud Shell (bash):
bash phase-1a-blob-storage.sh
bash phase-1c-servicebus.sh
bash phase-1b-function-eventgrid.sh
```

**Pros:** Nothing to install, always authenticated, works exactly as scripted
**Cons:** Need to upload files or paste content into the browser

---

### Option 3 — PowerShell Locally (Recommended for Windows) 💻
**Best for:** Running scripts from VS Code, repeatable demos, YouTube recordings

The `infra/` folder has both `.sh` (bash) and `.ps1` (PowerShell) versions of every script.
The `.ps1` files use PowerShell syntax (backtick `` ` `` for line continuation instead of `\`).

**One-time setup — Install Azure CLI:**
Download from: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows

**One-time setup — Allow local scripts to run:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Every session — Authenticate first:**
```powershell
.\infra\azure-login.ps1
```

**Then run any phase script:**
```powershell
.\infra\phase-1a-blob-storage.ps1
.\infra\phase-1c-servicebus.ps1
.\infra\phase-1b-function-eventgrid.ps1
```

**Pros:** Runs from VS Code terminal, scriptable, great for video demos
**Cons:** Requires Azure CLI installed locally

---

### Script Reference

| Script | What it creates | Run order |
|---|---|---|
| `azure-login.ps1` / (manual in portal) | Authenticates your session | Before anything else |
| `phase-1a-blob-storage.ps1/.sh` | Resource Group, Storage Account, Blob Container | 1st |
| `phase-1c-servicebus.ps1/.sh` | Service Bus Namespace, Topic, Subscriptions | 2nd |
| `phase-1b-function-eventgrid.ps1/.sh` | Function App, App Settings, Event Grid Subscription | 3rd (after deploying code) |

> **Note:** Phase 1b must be run **after** deploying the Function code (Step 3 in Phase 1b instructions), because Azure validates the Function endpoint URL when creating the Event Grid subscription.

---

## What Is CogniDocs?

CogniDocs is a **RAG (Retrieval-Augmented Generation) document platform** built on Azure.

A user uploads a document. The platform:
1. **Ingests** it via an event-driven pipeline (Azure Blob → Event Grid → Service Bus)
2. **Chunks & Embeds** the text using Azure OpenAI (Python worker)
3. **Stores** vectors in PostgreSQL (pgvector) and/or Cosmos DB
4. **Caches** hot embeddings in Redis
5. **Retrieves** answers to natural language questions using semantic search + LLM

The app is not just a study exercise — it is a **real-world enterprise pattern** used in production AI systems.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend API | Python + FastAPI | Main REST layer, document management |
| Frontend UI | Python + Streamlit | Upload, search, and demo interface |
| Primary vector DB | PostgreSQL + pgvector | Vector storage, RAG queries |
| NoSQL / vector DB | Azure Cosmos DB for NoSQL | Change feed, NoSQL vector patterns |
| Cache | Azure Managed Redis | Embedding cache, vector index |
| Eventing | Azure Event Grid | Trigger on file upload |
| Messaging | Azure Service Bus | Async job queue, dead-letter handling |
| Serverless | Azure Functions (Python) | Event-triggered workers |
| Containers | Azure Container Apps + AKS | Production hosting, KEDA autoscaling |
| Image registry | Azure Container Registry | Store and version Docker images |
| Secrets | Azure Key Vault | All credentials and connection strings |
| Config | Azure App Configuration | Feature flags, runtime config |
| Observability | OpenTelemetry + Azure Monitor | Distributed tracing, KQL queries |
| Auth | Azure Entra ID | Identity and access |
| Gateway | .NET Core (minimal) | File upload stream to Blob Storage |

---

## AI-200 Exam Coverage Map

The AI-200 exam has 4 domains. Every objective is covered in this project.

### Domain 3 — Connect to and Consume Azure Services (20–25%)

| Objective | Covered In | Status |
|---|---|---|
| Queue and process operations using Azure Service Bus (topics, subscriptions) | Phase 1 | ✅ Complete |
| Handle dead-letter queues | Phase 1 | ✅ Complete |
| Implement event-driven workflows using Event Grid (filters, custom events, retries) | Phase 1 | ✅ Complete |
| Build serverless APIs using Azure Functions (triggers and bindings) | Phase 1 | ✅ Complete |
| Configure and deploy function apps | Phase 1 | ✅ Complete |

---

## Phase Plan

### ✅ Phase 0 — Local Foundation
> **Cost: $0** | **AI-200 Objectives: None (scaffolding)**
>
> Build the local development environment. Everything runs on your machine before any Azure resource is created.

**What we build:**
- Docker Compose stack: PostgreSQL 16 with pgvector extension + Redis 7
- FastAPI backend: document upload endpoint, document list endpoint, health check
- Streamlit frontend: upload UI, document list, search placeholder
- Local file storage: uploaded documents saved to `api/uploads/`
- PostgreSQL `documents` table: tracks every uploaded file and its processing status

**Why PostgreSQL with pgvector from the start?**
The `pgvector/pgvector:pg16` Docker image is the same engine we will use in Azure (Azure Database for PostgreSQL). By running it locally first, every query and schema we write locally works identically in the cloud — no rewrites.

**Local services:**

| Service | Local address | Purpose |
|---|---|---|
| PostgreSQL | `localhost:5432` | Document metadata storage |
| Redis | `localhost:6379` | Cache (used in Phase 2C) |
| FastAPI | `http://localhost:8000` | REST API |
| FastAPI Docs | `http://localhost:8000/docs` | Swagger UI |
| Streamlit UI | `http://localhost:8501` | Frontend |

**Verified working on:** Python 3.14.2, Windows 11, Docker Desktop

**First-time setup:**

```powershell
# Terminal 1 — Start local databases (PostgreSQL + Redis via Docker)
cd C:\Work\AI-200\cogni-docs
docker compose up -d
docker ps   # confirm cognidocs-postgres and cognidocs-redis are running

# Terminal 2 — Set up and start the API
cd C:\Work\AI-200\cogni-docs\api
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload

# Terminal 3 — Set up and start the UI
cd C:\Work\AI-200\cogni-docs\ui
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

**After first-time setup (subsequent runs):**

```powershell
# Terminal 1
docker compose up -d

# Terminal 2
cd api && venv\Scripts\activate && python -m uvicorn main:app --reload

# Terminal 3
cd ui && venv\Scripts\activate && python -m streamlit run app.py
```

**Verify it's working:**
- `http://localhost:8000/health` → `{"status":"healthy","phase":"0 — Local Foundation"}`
- `http://localhost:8000/docs` → Swagger UI showing `/documents/upload` and `/documents/`
- `http://localhost:8501` → Streamlit app — upload a `.txt` file and confirm it appears in "My Documents"

---

### ✅ Phase 1 — Event & Messaging Pipeline
> **Cost: ~$10/month (Service Bus Standard)** | **AI-200 Domain: Connect to and Consume Azure Services (20–25%)**
> **YouTube Videos: #2 (Blob + Event Grid) · #3 (Azure Functions) · #4 (Service Bus + DLQ)**

The full pipeline built across three sub-phases:

```
Streamlit UI --> FastAPI --> Azure Blob Storage
                                    |
                             Event Grid (BlobCreated)
                                    |
                          Azure Function (Python v2)
                                    |
                          Service Bus Topic --> embedding-worker subscription
                                                        |
                                                   consumer.py
                                               (complete / dead-letter)
```

---

## Project Structure

```
cogni-docs/
├── docker-compose.yml       # Local PostgreSQL + Redis
├── .env                     # Local secrets (never committed)
├── .env.example             # Template (committed — no real secrets)
├── .gitignore
├── README.md                # This file
│
├── api/                     # FastAPI Python backend
│   ├── main.py              # App entry point, startup, health check
│   ├── database.py          # PostgreSQL connection and table setup
│   ├── documents.py         # Upload and list endpoints
│   └── requirements.txt
│
├── worker/                  # Python async worker (built in Phase 1)
│   └── requirements.txt
│
├── ui/                      # Streamlit frontend
│   ├── app.py               # Upload, list, search UI
│   └── requirements.txt
│
└── infra/                   # Azure setup scripts (added Phase 1+)
```

---

## Cost Summary

| Phase | Azure Services Running | Estimated Monthly Cost |
|---|---|---|
| Phase 0 | None (all local) | $0 |
| Phase 1 | Service Bus Standard | ~$10 |
| Phase 2A | + PostgreSQL Flexible Server B1ms | ~$22 |
| Phase 2B | + Cosmos DB (free tier) | ~$22 |
| Phase 2C | + Redis C0 Basic | ~$38 |
| Phase 3 | + ACR Basic; AKS only during study | ~$43 + ~$2/day AKS |
| Phase 4 | Key Vault + App Config (both near-free) | ~$43 |

> **Strategy:** Each phase is built sequentially. Services from earlier phases can be paused or deleted once the concept is learned and recorded. Total spend for the full study period: **~$25–50**.


---

## Troubleshooting

### `psycopg2-binary` fails to install — `pg_config executable not found`

**Cause:** `psycopg2-binary` versions older than 2.9.10 have no pre-built wheel for Python 3.12+.
When no wheel exists, pip tries to compile from C source — which requires `pg_config` and a C compiler. Windows has neither by default.

**Fix:** Use `psycopg2-binary>=2.9.10` in `requirements.txt`. This version ships pre-built `.whl` files for Python 3.12 and 3.13+.

```
# Wrong — breaks on Python 3.12+
psycopg2-binary==2.9.9

# Correct
psycopg2-binary>=2.9.10
```

---

### `numpy` fails to install — `Unknown compiler(s)`

**Cause:** `streamlit==1.35.0` depends on `numpy<2`, which resolves to `numpy 1.26.4`. That version has no pre-built wheel for Python 3.12+ and requires a C compiler (Meson build system) that isn't installed on Windows by default.

**Fix:** Use `streamlit>=1.40.0` which lifts the `numpy<2` constraint, allowing pip to install `numpy 2.x` which ships pre-built wheels for modern Python.

```
# Wrong — numpy<2 breaks on Python 3.12+
streamlit==1.35.0

# Correct
streamlit>=1.40.0
```

---

### `pip`, `uvicorn`, or `streamlit` not recognized in PowerShell

**Cause:** On Windows PowerShell, the `Scripts\` folder of a virtual environment is not always added to `PATH`, so bare commands like `pip` or `uvicorn` are not found even when the venv is activated.

**Fix:** Always prefix with `python -m`:

```powershell
# Instead of:   pip install      → use: python -m pip install
# Instead of:   uvicorn main:app → use: python -m uvicorn main:app
# Instead of:   streamlit run    → use: python -m streamlit run
```

---

### PowerShell script error: "The string is missing the terminator"

**Cause:** In PowerShell, the backtick `` ` `` is the line-continuation character and it **must** be the very last character on the line — even a single trailing space after it breaks parsing. This causes errors that show up many lines later as confusing string errors.

**Fix:** All `.ps1` scripts in this project have been rewritten to use single-line `az` commands — no backtick continuations at all. If you write your own PowerShell scripts, either keep `az` commands on one line or be very careful that no spaces follow a backtick.

```powershell
# Wrong — space after backtick breaks everything:
az group create ` 
  --name rg-test

# Correct — single line:
az group create --name rg-test --location eastus
```

---

### VS Code popup: "Would you like to create a virtual environment?"

**Cause:** VS Code detected a `requirements.txt` and offered to create a venv automatically.

**Fix:** If you already created a venv manually (as in this project), click **"Don't show again"** and dismiss. The venv you created is already correct. Letting VS Code create a second one causes conflicts.

---

---

### `func azure functionapp publish` error: "Can't determine project language"

**Cause:** Running `func azure functionapp publish` without specifying the language. The `func` CLI can't auto-detect Python from the files alone and requires an explicit flag.

**Fix:** Always include `--python` when publishing a Python function app:

```powershell
# Wrong -- language not specified:
func azure functionapp publish func-cognidocs

# Correct:
func azure functionapp publish func-cognidocs --python
```

---

### `az functionapp deployment source config-zip` returns `Bad Request`

**Cause:** For Linux Python Consumption plan Function Apps, `az ... config-zip` uses the wrong deployment endpoint and does not trigger a remote build. `pip install` never runs, so the Python worker fails to start with `No such file or directory` on `/home/site/wwwroot`.

**Fix:** Use the Azure Functions Core Tools CLI instead:

```powershell
# Install (choose one):
npm install -g azure-functions-core-tools@4 --unsafe-perm true
# or: winget install Microsoft.AzureFunctionsCoreTools

# Deploy from the worker/ directory:
cd worker
func azure functionapp publish func-cognidocs --python
cd ..
```

---

### Function App shows "No functions found" in portal

**Cause 1:** `host.json` contains JavaScript-style `//` comments. `host.json` must be **pure valid JSON** — no comments, no trailing text after the closing `}`. The Functions runtime parses this file at startup and crashes silently if it's invalid.

```json
// Wrong -- // comments are NOT valid JSON:
{
  "version": "2.0"
  // this breaks the runtime
}

// Correct -- pure JSON only:
{
  "version": "2.0"
}
```

**Cause 2:** Missing `AzureWebJobsFeatureFlags=EnableWorkerIndexing` app setting. The Python v2 programming model uses decorators (`@app.event_grid_trigger(...)`) to declare functions. Without this flag, the runtime uses the old v1 model which requires a separate `function.json` file per function — it won't find decorator-based functions at all.

**Fix:** Add the setting via CLI or Portal:

```powershell
az functionapp config appsettings set --name func-cognidocs --resource-group rg-cognidocs --settings "AzureWebJobsFeatureFlags=EnableWorkerIndexing"
```

---

### Event Grid subscription creation fails: "Webhook validation handshake failed"

**Cause:** The CLI command `az eventgrid event-subscription create --endpoint-type webhook` sends a validation HTTP request to the Function URL immediately. On a Consumption plan, the app is cold-started — it doesn't respond in time and the handshake fails.

**Fix:** Create the subscription via the Azure Portal using **"Azure Function"** as the endpoint type (not "Webhook"). The portal uses a different registration flow that doesn't require the live handshake.

Steps: Storage Accounts → `stcognidocs` → Events → `+ Event Subscription` → Endpoint Type: **Azure Function** → select `func-cognidocs` / `blob_created_handler`

Don't forget the **Filters tab**: enable subject filtering → Subject Begins With: `/blobServices/default/containers/documents/blobs/raw/`

---

### `ValueError: 'dead_letter' is not a valid ServiceBusSubQueue`

**Cause:** The `sub_queue` parameter in `get_subscription_receiver()` does not accept `"dead_letter"` (with underscore) or `"dead-letter"` (with hyphen). The Azure SDK enum uses `"deadletter"` as a single word with no separator.

**Fix:** Use `sub_queue="deadletter"` (no underscore):

```python
# Wrong -- both of these raise ValueError:
sub_queue="dead_letter"
sub_queue="dead-letter"

# Correct:
sub_queue="deadletter"

# Also correct -- use the enum directly to avoid guessing:
from azure.servicebus import ServiceBusSubQueue
sub_queue=ServiceBusSubQueue.DEAD_LETTER
```

The portal displays it as "Dead-letter" with a hyphen, which makes `"dead_letter"` seem right — it isn't. Always use `"deadletter"` or the `ServiceBusSubQueue.DEAD_LETTER` enum.

---
