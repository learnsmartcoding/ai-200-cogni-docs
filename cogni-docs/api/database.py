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

    We read it from .env so the password is never hardcoded in source code.
    """
    # os.getenv("POSTGRES_URL") reads POSTGRES_URL from environment variables.
    # If not found, it returns None — which would cause a connection error below.
    return psycopg2.connect(os.getenv("POSTGRES_URL"))


def init_db():
    """
    Creates the 'documents' table if it doesn't already exist.
    Called once at API startup (from main.py).

    FUTURE — Phase 2A will add this column to support vector search:
        embedding vector(1536)   ← stores AI-generated float arrays
    """
    # Open a connection to PostgreSQL
    conn = get_connection()

    # Create a cursor — the object that sends SQL to the database and reads results.
    # In .NET: var cmd = new SqlCommand(sql, conn);
    cursor = conn.cursor()

    # KEY PYTHON CONCEPT — Triple-quoted strings:
    # """ ... """ is Python's multiline string syntax.
    # Equivalent to C#'s verbatim string: @"..."
    # Used here to write a clean, readable multi-line SQL statement.
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
    # Notes on each column:
    #   SERIAL         = auto-incrementing integer, like IDENTITY(1,1) in SQL Server
    #   DEFAULT        = value used when no value is supplied on INSERT
    #   CURRENT_TIMESTAMP = PostgreSQL function that returns the current date+time
    #   IF NOT EXISTS  = safe to run every startup — skips silently if table exists

    # commit() saves the CREATE TABLE permanently to the database.
    # Without it, the table only exists for this connection session and is lost on close.
    # In EF Core this is: await context.SaveChangesAsync();
    conn.commit()

    # Always close cursor and connection to free up database resources.
    # In .NET, a 'using' statement does this automatically.
    # In Python, you close manually — or use a 'with' block (we'll refactor this later).
    cursor.close()
    conn.close()

    print("✅ Database ready")
