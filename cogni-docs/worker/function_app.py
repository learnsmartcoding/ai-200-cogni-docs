# =============================================================================
# function_app.py — Azure Function: Event Grid Trigger → Service Bus Publisher
# =============================================================================
#
# WHAT IS AN AZURE FUNCTION?
#   A serverless function is code that runs only when triggered by an event.
#   You don't manage any server — Azure runs it, scales it, and bills you only
#   for actual execution time. At study volumes, this is effectively free.
#
# THIS FUNCTION'S JOB (the full pipeline):
#   1. Azure fires this function automatically when a blob is created (Phase 1b)
#   2. The function reads the event to find out what file was uploaded
#   3. It publishes a processing job to a Service Bus topic (Phase 1c)
#   4. A worker (consumer.py) picks up that job and processes the document
#
# PROGRAMMING MODEL:
#   We use the Azure Functions Python v2 model.
#   V2 uses decorators (@app.event_grid_trigger) — similar to how FastAPI uses
#   @app.get() to register routes. Same concept, different Azure service.
#
# AI-200 OBJECTIVES COVERED:
#   ✅ Implement event-driven workflows using Azure Event Grid
#   ✅ Build serverless APIs using Azure Functions (triggers and bindings)
#   ✅ Configure and deploy function apps
#   ✅ Queue and process back-end operations using Azure Service Bus
# =============================================================================

import azure.functions as func   # Azure Functions SDK — provides trigger types, bindings
import logging                   # Python's built-in logging module (like ILogger in .NET)
import json                      # Built-in module to convert Python dicts ↔ JSON strings
import os                        # Built-in module to read environment variables
from azure.servicebus import ServiceBusClient, ServiceBusMessage
# ServiceBusClient    — connects to an Azure Service Bus namespace
# ServiceBusMessage   — represents one message to send to a topic/queue


# =============================================================================
# PHASE 1b — Event Grid Trigger
# =============================================================================
#
# FunctionApp() creates the app object — this is the entry point.
# All functions in this file are registered on this app object via decorators.
# Similar to how FastAPI's app = FastAPI() works.
# =============================================================================
app = func.FunctionApp()


@app.event_grid_trigger(arg_name="event")
def blob_created_handler(event: func.EventGridEvent):
    """
    Triggered automatically by Azure Event Grid when a new blob is created
    in our Storage Account container.

    Azure calls this function with the event details as the 'event' argument.
    We don't call this function ourselves — Azure does, whenever a file is uploaded.

    Args:
        event (EventGridEvent): The event object Azure passes in automatically.
                                Contains metadata about what happened (what blob,
                                when, which container, etc.)
    """
    # ── Phase 1b: Log the Event Grid event ────────────────────────────────────

    # logging.info() writes to Azure's Application Insights log stream.
    # In the Azure portal: Function App → Functions → Monitor → Logs
    # In .NET this would be: _logger.LogInformation(...)
    logging.info("=" * 60)
    logging.info("📬 Event Grid trigger fired — new blob detected")
    logging.info(f"   Event Type : {event.event_type}")
    # event.subject is the relative path to the blob, e.g.:
    # /blobServices/default/containers/documents/blobs/raw/abc123.pdf
    logging.info(f"   Subject    : {event.subject}")
    logging.info(f"   Event Time : {event.event_time}")
    logging.info(f"   Event ID   : {event.id}")

    # event.get_json() parses the event's data payload as a Python dict.
    # The data contains blob-specific details: URL, size, content type, ETag.
    event_data = event.get_json()
    logging.info(f"   Event Data : {json.dumps(event_data, indent=2)}")

    # Extract the blob URL from the event data
    # event_data["url"] looks like:
    # https://stcognidocs.blob.core.windows.net/documents/raw/abc123.pdf
    blob_url = event_data.get("url", "")

    # Split the URL by "/" and take the last part to get just the filename
    # "https://...blob.core.windows.net/documents/raw/abc123.pdf".split("/")
    # gives: ["https:", "", "...blob.core.windows.net", "documents", "raw", "abc123.pdf"]
    # [-1] takes the last element: "abc123.pdf"
    blob_name = blob_url.split("/")[-1]

    content_type = event_data.get("contentType", "unknown")
    size_bytes = event_data.get("contentLength", 0)

    logging.info(f"   Blob Name  : {blob_name}")
    logging.info(f"   Blob URL   : {blob_url}")
    logging.info(f"   Type       : {content_type}")
    logging.info(f"   Size       : {size_bytes} bytes")

    # Only process files in our "raw/" prefix (ignore any system blobs)
    # str.startswith() checks if a string begins with the given prefix
    if not event_data.get("url", "").endswith((".pdf", ".txt")):
        logging.warning("⚠️  Skipping — not a PDF or TXT file")
        return   # 'return' exits the function early (like 'return' in C#)

    # ── Phase 1c: Publish to Azure Service Bus ─────────────────────────────────

    # Build the message payload — this is what the worker will receive.
    # We use a Python dict and convert it to a JSON string for the message body.
    message_payload = {
        "blob_url": blob_url,
        "blob_name": blob_name,
        "content_type": content_type,
        "size_bytes": size_bytes,
        "event_time": str(event.event_time),
        "status": "pending_processing"
    }

    # Read Service Bus connection info from Azure Application Settings.
    # In Azure portal: Function App → Configuration → Application settings
    # These are equivalent to appsettings.json values in .NET
    sb_connection_str = os.environ.get("AzureServiceBusConnectionString")
    topic_name = os.environ.get("ServiceBusTopic", "document-processing")

    if not sb_connection_str:
        logging.error("❌ AzureServiceBusConnectionString not configured in Function App settings")
        return

    # KEY PYTHON CONCEPT — "with" as a context manager for Azure SDK clients:
    # The Azure SDK clients implement __enter__ and __exit__ methods.
    # Using 'with' ensures the connection is properly closed when the block ends,
    # even if an error occurs. Equivalent to C#'s 'using' statement.
    try:
        with ServiceBusClient.from_connection_string(sb_connection_str) as sb_client:

            # get_topic_sender() opens a sender scoped to a specific topic.
            # A topic is like a broadcast channel — multiple subscribers can
            # each receive a copy of every message. (vs a queue = one receiver)
            with sb_client.get_topic_sender(topic_name=topic_name) as sender:

                # Create the message — json.dumps() converts the Python dict to
                # a JSON string. The worker will parse this JSON on the other end.
                message = ServiceBusMessage(
                    body=json.dumps(message_payload),
                    # Application properties = metadata attached to the message
                    # Subscribers can filter by these without reading the full body
                    application_properties={
                        "blob_name": blob_name,
                        "content_type": content_type
                    }
                )

                # send_messages() publishes the message to the topic.
                # All subscriptions on this topic will receive a copy.
                sender.send_messages(message)

        logging.info(f"✅ Published to Service Bus topic '{topic_name}'")
        logging.info(f"   Workers will now pick up and embed: {blob_name}")

    # KEY PYTHON CONCEPT — catching specific exception types:
    # We catch Exception broadly here so a Service Bus failure doesn't
    # prevent the function from logging the event. In production you'd
    # use a retry policy — which Service Bus handles automatically.
    except Exception as e:
        logging.error(f"❌ Failed to publish to Service Bus: {str(e)}")
        # Re-raise so Azure Functions marks this execution as failed
        # A failed execution will be retried based on the host.json retry policy
        raise
