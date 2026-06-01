# CogniDocs
### Intelligent Document Processing & Semantic Search Platform

> **AI-200 Certification Study Project**
> Built phase by phase, covering every objective of the Microsoft AI-200 exam.
> Each phase = one or more exam objectives = one or more YouTube videos.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | **3.12 or higher** | Tested on 3.14.2. Use `python --version` to check. |
| Docker Desktop | Latest | Required for local PostgreSQL + Redis |
| VS Code | Latest | Recommended IDE |
| VS Code Extensions | — | Python, Docker, Azure Functions, REST Client, Azure Databases |

> **Windows note:** Always use `python -m pip`, `python -m uvicorn`, and `python -m streamlit` instead of bare `pip`, `uvicorn`, `streamlit`. This ensures commands use the active virtual environment on Windows PowerShell.

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
