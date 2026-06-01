# =============================================================================
# main.py — FastAPI Application Entry Point
# =============================================================================
#
# FastAPI is a modern Python web framework for building REST APIs.
# If you know ASP.NET Core, think of this file as your Program.cs —
# it creates the app, registers middleware/routes, and starts the server.
#
# KEY PYTHON CONCEPT — Imports:
#   "from x import y" is Python's version of C# "using" statements.
#   You only import what you need from a module, not the whole thing.
# =============================================================================

from fastapi import FastAPI       # The core FastAPI class — like WebApplication in .NET
from database import init_db      # Our custom function from database.py
from documents import router as docs_router  # Our /documents endpoints from documents.py


# -----------------------------------------------------------------------------
# Create the FastAPI app instance.
# This is equivalent to "var app = builder.Build()" in .NET.
# FastAPI automatically generates:
#   - Swagger UI at:       http://localhost:8000/docs
#   - OpenAPI JSON at:     http://localhost:8000/openapi.json
# No extra setup needed — it's built in.
# -----------------------------------------------------------------------------
app = FastAPI(
    title="CogniDocs API",
    description="Intelligent Document Processing & Semantic Search — AI-200 Study Project",
    version="0.1.0"
)


# -----------------------------------------------------------------------------
# KEY PYTHON CONCEPT — Decorators (@something):
#
# A decorator is a function that "wraps" another function to add behaviour.
# In .NET, you use Attributes like [HttpGet], [Authorize], [Route].
# In Python, decorators do the same thing but with the @ syntax.
#
# @app.on_event("startup") tells FastAPI:
#   "Run the function below ONCE when the server first starts up,
#    before accepting any requests."
# This is equivalent to app.Lifetime.ApplicationStarted in .NET.
# -----------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    """Runs once at server startup. Creates database tables if they don't exist."""
    init_db()   # Calls our function in database.py to set up PostgreSQL tables


# -----------------------------------------------------------------------------
# @app.get("/health") registers an HTTP GET endpoint at the /health URL path.
# The function directly below the decorator handles the request.
#
# In .NET this would look like:
#   [HttpGet("health")]
#   public IActionResult Health() { return Ok(new { status = "healthy" }); }
# -----------------------------------------------------------------------------
@app.get("/health")
def health():
    """
    Health check endpoint.
    Load balancers and Azure monitoring call this to verify the API is alive.
    """
    # Returning a Python dict from a FastAPI function automatically
    # serialises it to a JSON response — no need for JsonResult or Ok() like in .NET.
    return {
        "status": "healthy",
        "phase": "0 — Local Foundation",
        "next": "Phase 1 will add Event Grid + Service Bus"
    }


# -----------------------------------------------------------------------------
# Register the documents router.
# All routes defined in documents.py (prefixed with /documents) are now
# part of this app.
# Equivalent to app.MapControllers() in .NET — it wires up all controller routes.
# -----------------------------------------------------------------------------
app.include_router(docs_router)
