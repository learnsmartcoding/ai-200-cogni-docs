# =============================================================================
# send_test_message.py -- Publish test messages directly to Service Bus
# =============================================================================
#
# PURPOSE:
#   In the real pipeline, messages are published by the Azure Function when
#   a blob is uploaded. This script lets you publish messages manually to
#   test consumer.py and all 3 DLQ causes without needing to upload files.
#
# USAGE:
#   python send_test_message.py             -- normal message (completes cleanly)
#   python send_test_message.py fail        -- triggers Cause 2 (explicit dead-letter)
#   python send_test_message.py abandon     -- triggers Cause 1 (max delivery count)
#
# DLQ CAUSE DEMOS:
#
#   Cause 1 -- Max delivery count (Azure auto-DLQ after 3 failed attempts):
#     python send_test_message.py abandon
#     python consumer.py
#     Watch: delivery count 1 -> abandon -> 2 -> abandon -> 3 -> abandon -> AUTO DLQ
#     python consumer.py dlq  -> DLQ Reason: MaxDeliveryCountExceeded
#
#   Cause 2 -- Explicit dead_letter_message() by your code:
#     python send_test_message.py fail
#     python consumer.py
#     Watch: delivery count 1 -> immediately dead-lettered
#     python consumer.py dlq  -> DLQ Reason: ProcessingFailed
#
#   Cause 3 -- TTL expiry (cannot demo quickly, explain conceptually):
#     Message sits unread until its Time-To-Live expires (our topic TTL = 7 days).
#     Azure moves it to DLQ with reason: TTLExpiredException.
#     To test short-TTL: set time_to_live in ServiceBusMessage (see commented code below).
# =============================================================================

import os
import json
import sys
from datetime import timedelta
from dotenv import load_dotenv
from azure.servicebus import ServiceBusClient, ServiceBusMessage

load_dotenv(dotenv_path="../.env")

CONNECTION_STRING = os.getenv("AZURE_SERVICE_BUS_CONNECTION_STRING")
TOPIC_NAME        = os.getenv("AZURE_SERVICE_BUS_TOPIC", "document-processing")

if not CONNECTION_STRING:
    print("ERROR: AZURE_SERVICE_BUS_CONNECTION_STRING not set in .env")
    sys.exit(1)

# Parse command-line argument
mode = sys.argv[1] if len(sys.argv) > 1 else "normal"

if mode not in ("normal", "fail", "abandon"):
    print(f"ERROR: unknown mode '{mode}'")
    print("Usage: python send_test_message.py [normal|fail|abandon]")
    sys.exit(1)

# Build blob_name based on mode.
# consumer.py reads blob_name and checks for "fail" or "abandon" keywords.
if mode == "fail":
    blob_name = "raw/test-fail-document.pdf"
    mode_label = "CAUSE 2 -- explicit dead-letter"
    next_steps = [
        "python consumer.py        <- receives message, dead-letters immediately",
        "python consumer.py dlq    <- DLQ Reason: ProcessingFailed, Delivery Count: 1"
    ]
elif mode == "abandon":
    blob_name = "raw/test-abandon-document.pdf"
    mode_label = "CAUSE 1 -- max delivery count (Azure auto-DLQ)"
    next_steps = [
        "python consumer.py        <- watch delivery count 1->2->3 then auto-DLQ",
        "python consumer.py dlq    <- DLQ Reason: MaxDeliveryCountExceeded, Delivery Count: 3"
    ]
else:
    blob_name = "raw/test-normal-document.pdf"
    mode_label = "NORMAL -- will complete cleanly"
    next_steps = [
        "python consumer.py        <- receives message, completes it (removed from queue)"
    ]

payload = {
    "blob_url":     f"https://stcognidocs.blob.core.windows.net/documents/{blob_name}",
    "blob_name":    blob_name,
    "content_type": "application/pdf",
    "size_bytes":   12345,
    "event_time":   "2026-05-27T20:00:00Z",
    "status":       "pending"
}

sb_message = ServiceBusMessage(json.dumps(payload))

# =============================================================================
# CAUSE 3 DEMO (optional, uncomment to test short TTL):
# Sets the message TTL to 30 seconds. If no consumer reads it in 30s,
# Azure moves it to DLQ with reason "TTLExpiredException".
# Requires --enable-dead-lettering-on-message-expiration on the subscription.
# =============================================================================
sb_message.time_to_live = timedelta(seconds=5)
# mode_label += " + short TTL (30s) for Cause 3 demo"

print(f"\n📤 Publishing test message to Service Bus...")
print(f"   Topic:     {TOPIC_NAME}")
print(f"   blob_name: {blob_name}")
print(f"   Mode:      {mode_label}\n")

with ServiceBusClient.from_connection_string(CONNECTION_STRING) as client:
    with client.get_topic_sender(topic_name=TOPIC_NAME) as sender:
        sender.send_messages(sb_message)

print("   ✅ Message sent successfully.\n")
print("Next steps:")
for step in next_steps:
    print(f"   {step}")
print()
