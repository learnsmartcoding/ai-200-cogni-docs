# =============================================================================
# app.py — Streamlit Frontend
# =============================================================================
#
# Streamlit is a Python library that turns Python scripts into web UIs.
# You don't write HTML or JavaScript — everything is Python.
# Every time the user interacts (clicks a button, changes a dropdown),
# Streamlit reruns the entire script from top to bottom.
#
# Think of it as a live Python script that renders as a web page.
#
# LIBRARY: httpx
#   httpx is a Python HTTP client — used to call our FastAPI backend.
#   Equivalent to HttpClient in .NET or fetch() in JavaScript/Angular.
# =============================================================================

import streamlit as st   # The UI library — every st.something() renders something on screen
import httpx             # HTTP client — sends requests to our FastAPI backend

# The base URL of our FastAPI backend.
# All API calls will be prefixed with this.
API_URL = "http://localhost:8000"

# =============================================================================
# PAGE CONFIG — must be the first Streamlit call in the script.
# Sets the browser tab title, icon, and layout.
# =============================================================================
st.set_page_config(
    page_title="CogniDocs",
    page_icon="📄",
    layout="wide"    # "wide" uses the full browser width (vs "centered" which is narrower)
)

# st.title() renders a large H1 heading on the page
st.title("📄 CogniDocs")

# st.caption() renders small grey subtitle text below the title
st.caption("Intelligent Document Processing & Semantic Search — AI-200 Study Project")


# =============================================================================
# SIDEBAR NAVIGATION
# st.sidebar.radio() renders a set of radio buttons in the left sidebar.
# The selected option is returned as a string and stored in 'page'.
# Every time the user clicks a different option, the script reruns and
# 'page' has the new value — Streamlit handles the state automatically.
# =============================================================================
page = st.sidebar.radio(
    "Navigate",
    ["📤 Upload Document", "📋 My Documents", "🔍 Search (Phase 2)"]
)


# =============================================================================
# KEY PYTHON CONCEPT — if / elif / else:
# Python uses "elif" (not "else if") for chained conditions.
# This is the same as a switch/case on the selected page value.
# =============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1: Upload Document
# ─────────────────────────────────────────────────────────────────────────────
if page == "📤 Upload Document":
    st.header("Upload a Document")

    # st.info() renders a blue info banner
    st.info("Supported: PDF and TXT files")

    # st.file_uploader() renders a file picker widget.
    # type=["pdf", "txt"] restricts which files the user can select.
    # Returns None if no file is selected, or an UploadedFile object if one is.
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "txt"])

    # Only show the Upload button if a file has been selected
    if uploaded_file:
        # st.button() renders a clickable button and returns True when clicked.
        # type="primary" makes it the highlighted/blue button style.
        if st.button("Upload", type="primary"):

            # st.spinner() shows a loading indicator while the indented block runs.
            # The 'with' here is not file I/O — it's a Python context manager
            # that Streamlit uses to show/hide the spinner around a block of code.
            with st.spinner("Uploading..."):

                # KEY PYTHON CONCEPT — try / except:
                # Equivalent to try / catch in C#.
                # We wrap the HTTP call in try/except because the API might be
                # offline — we want to show a friendly error instead of crashing.
                try:
                    # httpx.post() sends an HTTP POST request.
                    # files= sets the multipart/form-data body — same as what
                    # a browser sends when you submit a file input form.
                    # uploaded_file.getvalue() reads the file bytes into memory.
                    response = httpx.post(
                        f"{API_URL}/documents/upload",
                        files={
                            "file": (
                                uploaded_file.name,       # Original filename
                                uploaded_file.getvalue(), # File content as bytes
                                uploaded_file.type        # MIME type e.g. "application/pdf"
                            )
                        },
                        timeout=30   # Raise an error if no response within 30 seconds
                    )

                    if response.status_code == 200:
                        # response.json() parses the JSON response body into a Python dict
                        result = response.json()

                        # st.success() renders a green success banner
                        # ** around text in Streamlit markdown makes it bold
                        st.success(f"✅ Uploaded! Document ID: **{result['id']}**")

                        # st.json() renders a formatted, collapsible JSON viewer
                        st.json(result)
                    else:
                        # st.error() renders a red error banner
                        st.error(f"Upload failed: {response.text}")

                # KEY PYTHON CONCEPT — Exception as e:
                # 'as e' captures the exception object so we can read its message.
                # Equivalent to 'catch (Exception ex)' in C#.
                except Exception as e:
                    st.error(f"Cannot reach API at {API_URL}. Is it running?\nError: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2: My Documents
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📋 My Documents":
    st.header("Uploaded Documents")

    # st.button() returns True for one script run when clicked
    if st.button("🔄 Refresh"):
        # st.rerun() forces Streamlit to rerun the entire script immediately,
        # which fetches fresh data from the API.
        st.rerun()

    try:
        # httpx.get() sends an HTTP GET request to the documents list endpoint
        response = httpx.get(f"{API_URL}/documents/", timeout=10)

        if response.status_code == 200:
            docs = response.json()  # Parse JSON array into a Python list of dicts

            if docs:
                # KEY PYTHON CONCEPT — for loop:
                # Iterates over every item in the list.
                # Equivalent to foreach (var doc in docs) in C#.
                for doc in docs:
                    # st.expander() creates a collapsible section.
                    # The 'with' block defines what appears inside it when expanded.
                    with st.expander(f"📄 {doc['filename']}  •  Status: `{doc['status']}`"):
                        st.json(doc)
            else:
                st.info("No documents uploaded yet. Go to Upload Document to add one.")
        else:
            st.error("Could not fetch documents from API.")

    except Exception as e:
        st.error(f"Cannot reach API. Is it running?\nError: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3: Semantic Search (placeholder — built in Phase 2)
# ─────────────────────────────────────────────────────────────────────────────
elif page == "🔍 Search (Phase 2)":
    st.header("Semantic Search")

    # st.warning() renders a yellow warning banner
    st.warning("🚧 Coming in Phase 2 — Vector Embeddings & PostgreSQL pgvector")

    # st.markdown() renders Markdown-formatted text
    st.markdown("""
    **What you'll be able to do in Phase 2:**
    - Ask: *"What does my document say about pricing?"*
    - The app generates a vector embedding of your question
    - Searches PostgreSQL using pgvector for the closest matching document chunks
    - Returns a grounded answer using RAG (Retrieval-Augmented Generation)

    **AI-200 objective covered:**
    *Run vector similarity search, implement RAG patterns using metadata filter*
    (Domain 2 — Azure Database for PostgreSQL, 25–30%)
    """)
