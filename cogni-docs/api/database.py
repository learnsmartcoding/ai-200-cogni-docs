# =============================================================================
# database.py — PostgreSQL Connection and Table Setup
# =============================================================================
#
# This file handles two things:
#   1. Opening a connection to PostgreSQL
#   2. Creating the database tables when the app starts
#
# LIBRARY: psycopg2
#   The most popular PostgreSQL driver for Python.
#   It is lower-level than Entity Framework — you write raw SQL yourself.
#   Think of it as SqlConnection + SqlCommand in .NET (similar to Dapper).
#
# KEY PYTHON CONCEPT — Modules and imports:
#   Python ships with a large standard library. "import os" gives you access
#   to operating system features (env vars, file paths, etc.) — no pip install needed.
#   Third-party packages like psycopg2 DO need pip install.
# =============================================================================

import psycopg2              # Third-party: PostgreSQL driver, installed via pip
import os                    # Built-in: access environment variables and file paths
from dotenv import load_dotenv   # Third-party: reads the .env file into environment variables


# -----------------------------------------------------------------------------
# load_dotenv() reads every line of the .env file and adds it as an
# environment variable — making values available via os.getenv() below.
#
# In .NET, this is automatic via appsettings.json + IConfiguration.
# In Python, you call it explicitly once, before any os.getenv() calls.
# -----------------------------------------------------------------------------
load_dotenv()


def get_connection():
    """
    Opens and returns a new PostgreSQL database connection.

    In .NET:
        var conn = new SqlConnection(connectionString);
        conn.Open();
        return conn;

    psycopg2.connect() takes a connection URL in this format:
        postgresql://username:password@host:port/database_name

    Phase 0: POSTGRES_URL points to local Docker PostgreSQL.
    Phase 2A: POSTGRES_URL switches to Azure PostgreSQL Flexible Server.
              The URL gains ?sslmode=require because Azure enforces TLS.
              No code change needed -- just update .env.

    We read it from .env so the password is never hardcoded in source code.
    """
    conn = psycopg2.connect(os.getenv("POSTGRES_URL"))

    # Register the pgvector type with this connection so psycopg2 can
    # deserialize 'vector' columns into Python lists/numpy arrays.
    # Only runs if the pgvector package is installed (Phase 2A+).
    if PGVECTOR_AVAILABLE:
        register_vector(conn)

    return conn


def init_db():
    """
    Creates all database tables if they don't already exist.
    Called once at API startup (from main.py lifespan handler).

    Tables created:
      - documents       : one row per uploaded file (Phase 0)
      - document_chunks : one row per text chunk with its embedding vector (Phase 2A)

    Safe to re-run: every statement uses IF NOT EXISTS / IF NOT EXISTS.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # -------------------------------------------------------------------------
    # Step 1: Enable the pgvector extension
    # -------------------------------------------------------------------------
    # pgvector adds the 'vector' column type to PostgreSQL.
    # Without this, CREATE TABLE ... embedding vector(1536) fails.
    #
    # Local Docker: pgvector/pgvector:pg16 image has the extension pre-installed.
    # Azure PostgreSQL: the extension is pre-installed but must be whitelisted via:
    #   az postgres flexible-server parameter set --name azure.extensions --value vector
    #   (done in phase-2a-postgres.ps1)
    #
    # IF NOT EXISTS makes this idempotent -- safe to call every startup.
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # -------------------------------------------------------------------------
    # Step 2: Create the documents table (Phase 0 — unchanged)
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id           SERIAL PRIMARY KEY,
            filename     VARCHAR(255) NOT NULL,
            content_type VARCHAR(100),
            file_path    VARCHAR(500),
            status       VARCHAR(50) DEFAULT 'uploaded',
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # SERIAL      = auto-incrementing integer (like IDENTITY(1,1) in SQL Server)
    # IF NOT EXISTS = skips silently if the table already exists -- safe on every restart

    # -------------------------------------------------------------------------
    # Step 3: Create the document_chunks table (Phase 2A — NEW)
    # -------------------------------------------------------------------------
    # Each row = one chunk of text from a document + its embedding vector.
    #
    # Why chunks instead of storing the whole document as one embedding?
    #   1. LLMs have a token limit (~8K for ada-002). A large PDF won't fit.
    #   2. Chunking lets us find the SPECIFIC paragraph that answers a question,
    #      not just "this document is related."
    #   3. Smaller chunks = more precise retrieval = better RAG answers.
    #
    # embedding vector(1536):
    #   - 'vector' is the pgvector type. The number is the dimension count.
    #   - Azure OpenAI text-embedding-ada-002 outputs exactly 1536 dimensions.
    #   - Each dimension is a float32. Total: 1536 * 4 bytes = ~6KB per chunk.
    #   - In .NET: conceptually like storing a float[] as a DB column.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_chunks (
            id           SERIAL PRIMARY KEY,
            document_id  INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index  INTEGER NOT NULL,
            chunk_text   TEXT NOT NULL,
            token_count  INTEGER,
            embedding    vector(1536),
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # ON DELETE CASCADE: when a document row is deleted, all its chunks are
    # automatically deleted too. Prevents orphaned chunk rows.
    # chunk_index: position of this chunk in the original document (0, 1, 2...)
    # token_count: how many tokens this chunk used (useful for monitoring cost)
    # embedding:   NULL until Phase 2A-2 processes the document and calls OpenAI

    # -------------------------------------------------------------------------
    # Step 4: Create indexes for query performance
    # -------------------------------------------------------------------------

    # Standard B-tree index on document_id — speeds up queries like:
    # "give me all chunks for document 42" (used in Phase 2A-2 processing)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_chunks_document_id
        ON document_chunks(document_id);
    """)

    # HNSW vector index — the core of fast similarity search (Phase 2A-3)
    #
    # HNSW = Hierarchical Navigable Small World
    #   A graph-based index that organises vectors so similar ones are
    #   connected. Think of it like a geographic map — cities (vectors) close
    #   to each other have roads (graph edges) between them.
    #
    # Why HNSW and not IVFFlat (the other pgvector index type)?
    #   IVFFlat requires a training step: you must load data first, then run
    #   VACUUM ANALYZE before it works. HNSW builds incrementally -- you can
    #   query it after adding just one row. Better for our use case.
    #
    # vector_cosine_ops: use cosine distance for similarity.
    #   Cosine measures the ANGLE between two vectors, not their magnitude.
    #   Standard for text embeddings -- same word in short vs long documents
    #   gets the same embedding angle regardless of document length.
    #
    # m = 16:             connections per node. Higher = better recall, more memory.
    # ef_construction=64: quality of index build. Higher = better index, slower build.
    #   These defaults are the pgvector recommended starting point.
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_chunks_embedding
        ON document_chunks USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("✅ Database ready (documents + document_chunks + HNSW index)")
