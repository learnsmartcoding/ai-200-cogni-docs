# =============================================================================
# documents.py — Document Upload and List Endpoints
# =============================================================================
#
# PHASE HISTORY:
#   Phase 0: saved uploaded files to local disk (uploads/ folder)
#   Phase 1a (NOW): saves files to Azure Blob Storage instead
#
# WHY BLOB STORAGE?
#   Local disk doesn't work in the cloud — containers are stateless and
#   restart frequently, wiping any saved files. Azure Blob Storage is the
#   cloud-native solution: durable, scalable, and accessible from anywhere.
#   It's the equivalent of AWS S3 or a shared network drive, but for Azure.
#
# AI-200 OBJECTIVE COVERED (Phase 1a):
#   This sets up the foundation for Event Grid in Phase 1b.
#   When a file lands in Blob Storage, Azure fires a BlobCreated event
#   automatically — our Function App will react to that event.
# =============================================================================

from fastapi import APIRouter, UploadFile, File, HTTPException
from database import get_connection
import os, uuid
from dotenv import load_dotenv

# azure-storage-blob is the official Azure SDK package for Blob Storage.
# BlobServiceClient is the top-level client — it connects to a Storage Account.
from azure.storage.blob import BlobServiceClient

# Load .env values (AZURE_STORAGE_CONNECTION_STRING, etc.) into environment
load_dotenv()

router = APIRouter(prefix="/documents", tags=["documents"])


# =============================================================================
# BLOB STORAGE CLIENT SETUP
# =============================================================================
# Read config from environment variables (set in .env file).
# Never hardcode connection strings — they contain credentials.

AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER", "documents")
# os.getenv("KEY", "default") returns "default" if KEY is not set.
# Here we default the container name to "documents" if not specified in .env.


def get_blob_service_client() -> BlobServiceClient:
    """
    Creates and returns an Azure Blob Storage client.

    BlobServiceClient is the entry point for all Blob Storage operations.
    It connects to a Storage Account using a connection string.

    The connection string contains the account name, account key, and endpoint.
    Format: DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;

    In .NET this would be:
        new BlobServiceClient(connectionString)
    """
    if not AZURE_STORAGE_CONNECTION_STRING:
        # Raise a clear error if the .env value is missing —
        # better than a cryptic Azure SDK error later.
        raise ValueError(
            "AZURE_STORAGE_CONNECTION_STRING is not set in your .env file. "
            "Run the Azure CLI command to get it and add it to .env."
        )

    # from_connection_string() is a class method (like a static factory in C#).
    # It parses the connection string and configures the client automatically.
    return BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)


# =============================================================================
# UPLOAD ENDPOINT — POST /documents/upload
# =============================================================================
@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Accepts a PDF or TXT file, uploads it to Azure Blob Storage,
    and records its metadata + Blob URL in PostgreSQL.

    CHANGE FROM PHASE 0:
      Before: saved to local 'uploads/' folder, stored local file path in DB
      Now:    uploads to Azure Blob Storage, stores the public Blob URL in DB

    After this endpoint returns, Azure will automatically fire a BlobCreated
    event — which we'll connect to an Azure Function in Phase 1b.
    """
    # ── Step 1: Validate file type ─────────────────────────────────────────
    allowed_types = ["application/pdf", "text/plain"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only PDF and .txt files are supported")

    # ── Step 2: Build a unique blob name ───────────────────────────────────
    # Blob Storage is a flat key-value store — there are no real folders,
    # just names. We prefix with "raw/" to logically organise files.
    # e.g. "raw/3f2a1b9c-4e7d.pdf"
    file_id = str(uuid.uuid4())
    extension = os.path.splitext(file.filename)[1]
    blob_name = f"raw/{file_id}{extension}"
    # "raw/" prefix means: this is the original uploaded file, not yet processed.
    # Phase 2 workers will produce "chunks/" blobs alongside these.

    # ── Step 3: Upload to Azure Blob Storage ───────────────────────────────
    try:
        # Get a client for the whole Storage Account
        blob_service = get_blob_service_client()

        # Get a client scoped to our specific container ("documents")
        # A container is like a bucket — it holds a collection of blobs.
        container_client = blob_service.get_container_client(AZURE_STORAGE_CONTAINER)

        # Get a client for this specific blob (the file we're uploading)
        blob_client = container_client.get_blob_client(blob_name)

        # upload_blob() streams the file to Azure.
        # file.file is a file-like stream object (similar to Stream in .NET).
        # overwrite=True means: replace if a blob with this name already exists.
        blob_client.upload_blob(file.file, overwrite=True)

        # After upload, blob_client.url gives us the full HTTPS URL to the blob.
        # Example: https://stcognidocs.blob.core.windows.net/documents/raw/3f2a...pdf
        blob_url = blob_client.url

    # KEY PYTHON CONCEPT — "except ExceptionType as e":
    # Catches a specific type of exception (not all exceptions).
    # This is like "catch (Azure.RequestFailedException ex)" in C#.
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload to Azure Blob Storage: {str(e)}"
        )

    # ── Step 4: Record metadata in PostgreSQL ──────────────────────────────
    # We now store the Blob URL in file_path instead of a local disk path.
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO documents (filename, content_type, file_path, status)
        VALUES (%s, %s, %s, %s)
        RETURNING id, created_at
        """,
        (file.filename, file.content_type, blob_url, "uploaded")
        #                                  ^^^^^^^^
        #                                  blob_url instead of local file_path
    )
    doc_id, created_at = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()

    # ── Step 5: Return the result ──────────────────────────────────────────
    return {
        "id": doc_id,
        "filename": file.filename,
        "blob_name": blob_name,
        "blob_url": blob_url,
        "status": "uploaded",
        "created_at": str(created_at),
        "next": "Azure Event Grid will detect this blob and trigger the Function App (Phase 1b)"
    }


# =============================================================================
# LIST ENDPOINT — GET /documents/
# =============================================================================
@router.get("/")
async def list_documents():
    """
    Returns all uploaded documents from PostgreSQL, newest first.
    The file_path column now contains Azure Blob URLs instead of local paths.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, filename, content_type, file_path, status, created_at "
        "FROM documents ORDER BY created_at DESC"
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        {
            "id":           row[0],
            "filename":     row[1],
            "content_type": row[2],
            "blob_url":     row[3],   # Was file_path in Phase 0, now a Blob URL
            "status":       row[4],
            "created_at":   str(row[5])
        }
        for row in rows
    ]
