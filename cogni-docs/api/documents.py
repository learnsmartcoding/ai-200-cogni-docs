# =============================================================================
# documents.py — Document Upload and List Endpoints
# =============================================================================
#
# Defines the REST endpoints under /documents using FastAPI's APIRouter.
# APIRouter groups related endpoints — like a .NET Controller class.
#
# PHASE ROADMAP for this file:
#   Phase 0 (now):  save file to local disk, record in PostgreSQL
#   Phase 1:        save file to Azure Blob Storage instead of local disk
#   Phase 2:        after saving, trigger embedding generation via the worker
#
# KEY PYTHON CONCEPT — "from x import y":
#   Imports only specific symbols from a module, not everything.
#   Equivalent to C# "using" — but in Python you can be selective per import.
# =============================================================================

from fastapi import APIRouter, UploadFile, File, HTTPException
# APIRouter   — groups related routes, like a .NET Controller
# UploadFile  — represents a file sent via multipart/form-data
# File        — parameter marker that tells FastAPI to expect a file input
# HTTPException — returns HTTP error responses (like BadRequest() in .NET)

from database import get_connection   # Our PostgreSQL helper defined in database.py

# KEY PYTHON CONCEPT — importing multiple modules on one line:
# "import os, shutil, uuid" is shorthand for three separate import statements.
# Commonly used for small standard-library modules.
import os       # File path utilities: os.path.join, os.makedirs, os.path.splitext
import shutil   # File stream copy utility: shutil.copyfileobj
import uuid     # Generates random unique IDs — like Guid.NewGuid() in C#


# -----------------------------------------------------------------------------
# Create the router.
# prefix="/documents" means every route in this file starts with /documents.
# tags=["documents"] groups all these routes under one section in Swagger UI.
# -----------------------------------------------------------------------------
router = APIRouter(prefix="/documents", tags=["documents"])

# Local folder where uploaded files are saved (Phase 0 only).
# Phase 1 will replace this with Azure Blob Storage.
UPLOAD_DIR = "uploads"

# os.makedirs creates the folder if it doesn't exist yet.
# exist_ok=True means: don't raise an error if it already exists.
# Equivalent to Directory.CreateDirectory() in .NET — safe to call repeatedly.
os.makedirs(UPLOAD_DIR, exist_ok=True)


# -----------------------------------------------------------------------------
# @router.post("/upload") registers an HTTP POST endpoint at /documents/upload
#
# KEY PYTHON CONCEPT — Decorators:
# The @ symbol marks a decorator. It wraps the function below it with extra
# behaviour — in this case, registering it as a POST route in FastAPI.
# In .NET: [HttpPost("upload")] on a controller method does the same thing.
# -----------------------------------------------------------------------------
@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Accepts a PDF or TXT file upload, saves it to disk, and records
    its metadata in PostgreSQL.

    Args:
        file (UploadFile): The uploaded file from the HTTP request.
                           FastAPI automatically parses the multipart/form-data body.
                           File(...) means this parameter is REQUIRED.
                           The '...' (Ellipsis) is Python's built-in way to mark
                           something as mandatory — similar to [Required] in .NET.
    """
    # ── Step 1: Validate file type ─────────────────────────────────────────
    # file.content_type is the MIME type sent by the browser, e.g. "application/pdf"
    allowed_types = ["application/pdf", "text/plain"]

    # KEY PYTHON CONCEPT — "in" operator:
    # "x not in list" checks whether x is absent from the list.
    # Equivalent to: !allowedTypes.Contains(file.ContentType) in C#
    if file.content_type not in allowed_types:
        # HTTPException raises an HTTP error response and stops execution.
        # status_code=400 is "Bad Request" — same as return BadRequest(...) in .NET.
        raise HTTPException(status_code=400, detail="Only PDF and .txt files are supported")

    # ── Step 2: Build a unique file path ───────────────────────────────────
    # Generate a random ID so two files named "report.pdf" don't overwrite each other.
    # str(uuid.uuid4()) produces something like: "3f2a1b9c-4e7d-4a8f-b6c5-d2e1f0a9b8c7"
    file_id = str(uuid.uuid4())

    # os.path.splitext("report.pdf") returns the tuple ("report", ".pdf")
    # [1] takes the second element — the extension including the dot.
    extension = os.path.splitext(file.filename)[1]

    # KEY PYTHON CONCEPT — f-strings:
    # f"..." is Python's string interpolation (like $"..." in C#).
    # {file_id} and {extension} are replaced with their values at runtime.
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{extension}")
    # Result example: "uploads/3f2a1b9c-4e7d-4a8f-b6c5-d2e1f0a9b8c7.pdf"

    # ── Step 3: Save the file to disk ──────────────────────────────────────
    # KEY PYTHON CONCEPT — "with" statement:
    # 'with open(...) as buffer' opens a file and automatically closes it when
    # the indented block finishes — even if an error occurs.
    # This is Python's equivalent of C#'s 'using (var stream = File.OpenWrite(...))'.
    #
    # "wb" means: open for Writing in Binary mode (needed for PDFs and any non-text file).
    with open(file_path, "wb") as buffer:
        # shutil.copyfileobj reads from the upload stream (file.file) and writes
        # it to our local file (buffer) in chunks — memory-efficient for large files.
        shutil.copyfileobj(file.file, buffer)

    # ── Step 4: Record metadata in PostgreSQL ──────────────────────────────
    conn = get_connection()    # Open a database connection
    cursor = conn.cursor()     # Create a cursor to run SQL

    # Execute a parameterised INSERT statement.
    # %s are placeholders — psycopg2 safely substitutes the tuple values in order.
    # This prevents SQL injection, the same as using SqlParameter in .NET.
    # RETURNING id, created_at tells PostgreSQL to give back the auto-generated values.
    cursor.execute(
        """
        INSERT INTO documents (filename, content_type, file_path, status)
        VALUES (%s, %s, %s, %s)
        RETURNING id, created_at
        """,
        (file.filename, file.content_type, file_path, "uploaded")
        # This tuple maps to the four %s placeholders in the SQL above, in order.
    )

    # KEY PYTHON CONCEPT — tuple unpacking:
    # cursor.fetchone() returns one row as a tuple, e.g. (42, datetime(2025, 5, 26, ...))
    # "doc_id, created_at = ..." unpacks the tuple into two separate variables.
    # In C# this is: var (docId, createdAt) = (row[0], row[1]);
    doc_id, created_at = cursor.fetchone()

    conn.commit()     # Save the INSERT permanently
    cursor.close()    # Release the cursor
    conn.close()      # Release the connection

    # ── Step 5: Return the result as JSON ──────────────────────────────────
    # Returning a Python dict from FastAPI automatically serialises it to JSON.
    return {
        "id": doc_id,
        "filename": file.filename,
        "status": "uploaded",
        "created_at": str(created_at),   # str() converts the datetime object to a readable string
        "message": "Stored locally. In Phase 1 this will go to Azure Blob Storage."
    }


# -----------------------------------------------------------------------------
# @router.get("/") registers a GET endpoint at /documents/
# -----------------------------------------------------------------------------
@router.get("/")
async def list_documents():
    """
    Returns all uploaded documents from PostgreSQL, newest first.
    Equivalent to a GetAll() repository method in .NET.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # SELECT all rows, ordered newest-first (DESC = descending order)
    cursor.execute(
        "SELECT id, filename, content_type, status, created_at FROM documents ORDER BY created_at DESC"
    )

    # fetchall() returns every matching row as a list of tuples.
    # Example: [(1, "report.pdf", "application/pdf", "uploaded", datetime(...)), ...]
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # KEY PYTHON CONCEPT — List comprehension:
    # [ expression  for item in iterable ]
    # Builds a new list by running 'expression' for every 'item' in 'iterable'.
    # This is equivalent to LINQ's .Select() in C#:
    #   rows.Select(row => new { id = row[0], filename = row[1], ... }).ToList()
    return [
        {
            "id":           row[0],
            "filename":     row[1],
            "content_type": row[2],
            "status":       row[3],
            "created_at":   str(row[4])
        }
        for row in rows   # Iterates over every tuple in the rows list
    ]
