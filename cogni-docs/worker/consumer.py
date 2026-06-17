# =============================================================================
# consumer.py -- Azure Service Bus Consumer + Dead Letter Queue Demo
# =============================================================================
#
# WHAT IS THIS FILE?
#   A standalone Python script that reads messages from our Service Bus topic
#   subscription and demonstrates all three ways a message lands in the DLQ.
#
# AI-200 OBJECTIVES COVERED:
#   - Queue and process back-end operations using Azure Service Bus
#   - Dead-letter queue (DLQ) handling (all 3 causes)
#   - Message settlement patterns: complete, dead_letter, abandon
#   - Topics and subscriptions
#
# =============================================================================
# DEAD LETTER QUEUE (DLQ) -- ALL 3 CAUSES
# =============================================================================
#
# The DLQ is a built-in sub-queue on every Service Bus subscription.
# Messages land there when they cannot be processed. Three causes:
#
# CAUSE 1 -- Max delivery count exceeded (Azure does it automatically)
# -----------------------------------------------------------------------
#   A message is delivered but never successfully settled (consumer crashes,
#   or explicitly calls abandon_message()). After N failed attempts, Azure
#   automatically moves it to the DLQ.
#   max-delivery-count is set per subscription (we set 3).
#   DLQ Reason set by Azure: "MaxDeliveryCountExceeded"
#
#   Real world: transient failures -- network timeout, DB temporarily down.
#   You abandon so it retries. After too many retries it goes to DLQ.
#
#   Demo: python send_test_message.py abandon
#         python consumer.py
#         Watch: delivery count increments 1 -> 2 -> 3 -> auto DLQ
#
# CAUSE 2 -- Explicit dead_letter_message() call (your code does it)
# -----------------------------------------------------------------------
#   You decide the message is a poison message -- it will NEVER succeed
#   no matter how many retries. You dead-letter it immediately on delivery 1.
#   DLQ Reason set by YOUR code: whatever string you pass as `reason=`
#
#   Real world: corrupt data, wrong format, unsupported file type.
#   No point retrying -- dead-letter immediately and alert an operator.
#
#   Demo: python send_test_message.py fail
#         python consumer.py
#         Watch: 1 delivery -> immediately dead-lettered
#
# CAUSE 3 -- Message TTL expired with dead-lettering on expiration enabled
# -----------------------------------------------------------------------
#   Every message has a Time-To-Live (TTL). If no consumer reads it before
#   TTL expires AND the subscription has dead-lettering on expiration enabled
#   (we set --enable-dead-lettering-on-message-expiration), Azure moves it
#   to DLQ instead of silently dropping it.
#   DLQ Reason set by Azure: "TTLExpiredException"
#
#   Real world: a consumer went offline for days. Messages piled up and expired.
#   The DLQ lets you find and replay them instead of losing data silently.
#
#   Demo: cannot demo quickly -- requires waiting for the message TTL to expire
#         (default TTL on our topic is P7D = 7 days). Explain conceptually.
#         To test: create a test message with a short TTL, wait for it to expire.
#
# =============================================================================
# HOW TO RUN:
#   cd worker && venv\Scripts\activate
#   python consumer.py                  <- normal: receive and settle messages
#   python consumer.py dlq              <- peek the Dead Letter Queue
# =============================================================================

import os
import json
import time
from dotenv import load_dotenv
from azure.servicebus import ServiceBusClient
from azure.servicebus.exceptions import MessageAlreadySettled

load_dotenv(dotenv_path="../.env")

SERVICE_BUS_CONNECTION_STRING = os.getenv("AZURE_SERVICE_BUS_CONNECTION_STRING")
TOPIC_NAME        = os.getenv("AZURE_SERVICE_BUS_TOPIC", "document-processing")
SUBSCRIPTION_NAME = os.getenv("AZURE_SERVICE_BUS_SUBSCRIPTION", "embedding-worker")

# How long to wait for a message before looping again.
MAX_WAIT_TIME = 5


def process_message(message_body: dict, delivery_count: int):
    """
    Simulates processing a document job.
    Returns one of three string values to drive the settlement decision:

      "complete"    - processing succeeded, remove message permanently
      "deadletter"  - poison message, move to DLQ immediately (Cause 2)
      "abandon"     - transient failure, return to queue for retry (Cause 1 demo)

    In Phase 2 this will actually:
      1. Download blob from Azure Blob Storage
      2. Extract text from PDF/TXT
      3. Chunk text into overlapping segments
      4. Call Azure OpenAI to generate embeddings
      5. Store chunks + vectors in PostgreSQL (pgvector)
    """
    blob_name = message_body.get("blob_name", "")

    print(f"\n📄 Processing document: {blob_name}")
    print(f"   URL:            {message_body.get('blob_url')}")
    print(f"   Type:           {message_body.get('content_type')}")
    print(f"   Size:           {message_body.get('size_bytes')} bytes")
    print(f"   Delivery count: {delivery_count}")

    time.sleep(1)

    # -------------------------------------------------------------------------
    # CAUSE 2 DEMO: blob_name contains "fail"
    # Simulates a poison message -- bad data that will never succeed.
    # We dead-letter immediately without retrying.
    # -------------------------------------------------------------------------
    if "fail" in blob_name.lower():
        print("   ❌ Poison message detected -- dead-lettering immediately (Cause 2)")
        print("      Reason: this document is corrupt and will never process successfully")
        return "deadletter"

    # -------------------------------------------------------------------------
    # CAUSE 1 DEMO: blob_name contains "abandon"
    # Simulates a transient failure -- e.g. database temporarily unavailable.
    # We abandon so Service Bus retries. After max-delivery-count (3), Azure
    # automatically moves it to DLQ with reason "MaxDeliveryCountExceeded".
    # -------------------------------------------------------------------------
    if "abandon" in blob_name.lower():
        print(f"   ⚠️  Transient failure simulated -- abandoning (Cause 1)")
        print(f"      Delivery {delivery_count}/3: message returned to queue for retry")
        if delivery_count >= 3:
            print("      This is delivery 3 -- Azure will move it to DLQ after this abandon")
        return "abandon"

    # Happy path: processing succeeded
    print("   ✅ Processing complete (embedding will be stored in Phase 2)")
    return "complete"


def receive_messages():
    """
    Main consumer loop. Receives messages and settles them based on
    the result of process_message().

    Settlement options:
      complete_message()    -- success, permanently remove from queue
      dead_letter_message() -- poison message, move to DLQ (Cause 2)
      abandon_message()     -- transient failure, return to queue for retry (Cause 1)

    If a message is received but never settled (e.g. consumer crashes),
    the lock expires and Service Bus returns it to the queue automatically.
    After max-delivery-count retries, it moves to DLQ (Cause 1).
    """
    if not SERVICE_BUS_CONNECTION_STRING:
        print("ERROR: AZURE_SERVICE_BUS_CONNECTION_STRING not set in .env")
        return

    print(f"🔌 Connecting to Service Bus...")
    print(f"   Topic:        {TOPIC_NAME}")
    print(f"   Subscription: {SUBSCRIPTION_NAME}")
    print(f"   Max delivery count: 3 (set on subscription)")
    print(f"   Waiting for messages (Ctrl+C to stop)...\n")

    with ServiceBusClient.from_connection_string(SERVICE_BUS_CONNECTION_STRING) as client:
        receiver = client.get_subscription_receiver(
            topic_name=TOPIC_NAME,
            subscription_name=SUBSCRIPTION_NAME
        )

        with receiver:
            while True:
                messages = receiver.receive_messages(
                    max_message_count=10,
                    max_wait_time=MAX_WAIT_TIME
                )

                if not messages:
                    print("⏳ No messages -- waiting...")
                    continue

                for message in messages:
                    try:
                        raw_body = b"".join(message.body)
                        message_body = json.loads(raw_body.decode("utf-8"))

                        # delivery_count starts at 1 on first delivery.
                        # Increments each time the message is returned to queue.
                        # When it reaches max-delivery-count (3), Azure auto-DLQs.
                        delivery_count = message.delivery_count

                        print(f"\n📨 Received message (ID: {message.message_id})")

                        result = process_message(message_body, delivery_count)

                        if result == "complete":
                            # Happy path: permanently remove from queue.
                            # Message is gone -- cannot be received again.
                            receiver.complete_message(message)
                            print(f"   ✅ Message completed -- removed from queue permanently")

                        elif result == "deadletter":
                            # Cause 2: explicit dead-letter by our code.
                            # `reason` and `error_description` are stored in the DLQ
                            # and visible when you peek -- useful for debugging.
                            receiver.dead_letter_message(
                                message,
                                reason="ProcessingFailed",
                                error_description="Document is corrupt -- cannot be processed"
                            )
                            print(f"   💀 Message dead-lettered (Cause 2 -- explicit)")
                            print(f"      Check DLQ: python consumer.py dlq")
                            print(f"      Portal: Service Bus -> {TOPIC_NAME} -> {SUBSCRIPTION_NAME} -> Dead-letter tab")

                        elif result == "abandon":
                            # Cause 1 demo: return message to queue for retry.
                            # Service Bus increments delivery_count each time.
                            # Once delivery_count hits max-delivery-count (3),
                            # Azure automatically moves it to DLQ -- we don't code that.
                            receiver.abandon_message(message)
                            print(f"   🔄 Message abandoned -- returned to queue (delivery count was {delivery_count})")
                            if delivery_count >= 3:
                                print(f"   💀 Delivery count reached max (3) -- Azure will auto-DLQ this message")
                                print(f"      Run: python consumer.py dlq  to see it there")

                    except MessageAlreadySettled:
                        print(f"   ⚠️  Message lock expired before settlement -- would retry in production")

                    except Exception as e:
                        print(f"   ❌ Unexpected error: {e}")
                        try:
                            receiver.abandon_message(message)
                        except MessageAlreadySettled:
                            pass


def peek_dead_letter_queue():
    """
    Peeks at all messages in the DLQ without consuming or removing them.

    KEY THINGS TO OBSERVE in the output:
      DLQ Reason for Cause 1: "MaxDeliveryCountExceeded" (set by Azure)
      DLQ Reason for Cause 2: "ProcessingFailed"         (set by our code)
      DLQ Reason for Cause 3: "TTLExpiredException"      (set by Azure)

    Delivery count in DLQ:
      Cause 1: delivery count = 3 (hit the max)
      Cause 2: delivery count = 1 (dead-lettered on first delivery)
      Cause 3: delivery count = 1 (expired before any delivery attempt)

    Portal path to same view:
      Service Bus -> sb-cognidocs -> Topics -> document-processing
      -> Subscriptions -> embedding-worker -> Dead-letter tab
    """
    if not SERVICE_BUS_CONNECTION_STRING:
        print("ERROR: AZURE_SERVICE_BUS_CONNECTION_STRING not set in .env")
        return

    print(f"\n🔍 Peeking at Dead Letter Queue...")
    print(f"   Topic:        {TOPIC_NAME}")
    print(f"   Subscription: {SUBSCRIPTION_NAME}")
    print(f"   Note: peek is non-destructive -- messages stay in DLQ\n")

    with ServiceBusClient.from_connection_string(SERVICE_BUS_CONNECTION_STRING) as client:
        dlq_receiver = client.get_subscription_receiver(
            topic_name=TOPIC_NAME,
            subscription_name=SUBSCRIPTION_NAME,
            sub_queue="deadletter"   # "deadletter" (no underscore/hyphen) is the correct value
        )

        with dlq_receiver:
            dead_letters = dlq_receiver.peek_messages(max_message_count=10)

            if not dead_letters:
                print("   Dead Letter Queue is empty ✅")
                return

            print(f"   Found {len(dead_letters)} message(s) in DLQ:\n")
            for i, msg in enumerate(dead_letters, 1):
                raw_body = b"".join(msg.body)
                body_preview = raw_body.decode("utf-8")[:150]

                # Infer which cause put this message here based on the DLQ reason
                reason = msg.dead_letter_reason or "unknown"
                if reason == "MaxDeliveryCountExceeded":
                    cause = "Cause 1 -- max delivery count hit (Azure auto-DLQ)"
                elif reason == "TTLExpiredException":
                    cause = "Cause 3 -- message TTL expired (Azure auto-DLQ)"
                else:
                    cause = "Cause 2 -- explicit dead_letter_message() by your code"

                print(f"   --- Message {i} ---")
                print(f"   Message ID     : {msg.message_id}")
                print(f"   DLQ Reason     : {reason}")
                print(f"   DLQ Detail     : {msg.dead_letter_error_description}")
                print(f"   Delivery Count : {msg.delivery_count}")
                print(f"   Cause          : {cause}")
                print(f"   Body (preview) : {body_preview}...")
                print()


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "dlq":
        peek_dead_letter_queue()
    else:
        receive_messages()
