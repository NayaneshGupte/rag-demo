# RabbitMQ Quick Start Guide

Get started with RabbitMQ for the RAG demo in minutes!

## Prerequisites

- **Docker** and **Docker Compose** installed
- **Python 3.12+**
- **4 GB RAM** available for Docker

## Quick Start

### 1. Start RabbitMQ

```bash
# From project root
docker-compose -f docker-compose.rabbitmq.yml up -d

# Wait 30 seconds for RabbitMQ to start
docker-compose -f docker-compose.rabbitmq.yml ps
```

**Expected output:**
```
NAME                STATUS              PORTS
rabbitmq-server     Up (healthy)        0.0.0.0:5672->5672/tcp, 0.0.0.0:15672->15672/tcp
redis-cache         Up (healthy)        0.0.0.0:6379->6379/tcp
```

### 2. Access Management UI

Open your browser:

```
http://localhost:15672
```

**Credentials**:
- Username: `admin`
- Password: `admin123`

You should see the RabbitMQ Management dashboard!

### 3. Create Queues

You can create queues either via the UI or programmatically.

#### Option A: Via Management UI

1. Navigate to **Queues** tab
2. Click **Add a new queue**
3. Create these queues:
   - `emails.to_classify` (with priority and DLX)
   - `emails.to_respond`
   - `emails.to_send`
   - `documents.to_ingest`
   - `dead_letter_queue`

#### Option B: Via Python (Recommended)

```bash
pip install pika
python -m app.utils.setup_rabbitmq_queues
```

### 4. Install Python Dependencies

```bash
pip install pika==1.3.2 redis==5.0.1
```

### 5. Update Environment Variables

Add to your `.env` file:

```env
# RabbitMQ Configuration
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASS=admin123
RABBITMQ_VHOST=/
RABBITMQ_ENABLED=true

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_ENABLED=false  # Optional, for caching
```

## Testing the Setup

### Test 1: Publish a Message

Create a test script `test_publish.py`:

```python
import pika
import json
from datetime import datetime

# Connect to RabbitMQ
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host='localhost',
        port=5672,
        credentials=pika.PlainCredentials('admin', 'admin123')
    )
)
channel = connection.channel()

# Declare queue (idempotent)
channel.queue_declare(queue='emails.to_classify', durable=True)

# Test email event
test_email = {
    "email_id": "test-123",
    "from": "customer@example.com",
    "subject": "Test Email",
    "body": "This is a test email for RabbitMQ",
    "timestamp": datetime.utcnow().isoformat()
}

# Publish message
channel.basic_publish(
    exchange='',
    routing_key='emails.to_classify',
    body=json.dumps(test_email),
    properties=pika.BasicProperties(
        delivery_mode=2,  # Make message persistent
        priority=5  # Medium priority
    )
)

print(f"✅ Published test email to queue")
connection.close()
```

Run it:

```bash
python test_publish.py
```

### Test 2: Consume the Message

Create `test_consume.py`:

```python
import pika
import json

def callback(ch, method, properties, body):
    email = json.loads(body)
    print(f"\n✅ Received message:")
    print(f"   Email ID: {email['email_id']}")
    print(f"   From: {email['from']}")
    print(f"   Subject: {email['subject']}")
    
    # Acknowledge the message
    ch.basic_ack(delivery_tag=method.delivery_tag)
    print("   Message acknowledged ✓")

# Connect
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host='localhost',
        credentials=pika.PlainCredentials('admin', 'admin123')
    )
)
channel = connection.channel()

# Start consuming
print("🔍 Waiting for messages... (Press Ctrl+C to exit)")
channel.basic_consume(
    queue='emails.to_classify',
    on_message_callback=callback
)

try:
    channel.start_consuming()
except KeyboardInterrupt:
    print("\nStopping consumer...")
    channel.stop_consuming()
    connection.close()
```

Run it:

```bash
python test_consume.py
```

You should see the message received and acknowledged!

## Monitoring

### Check Queue Status

**Via UI**:
- Go to **Queues** tab
- See message counts, rates, and consumers

**Via CLI**:
```bash
docker exec rabbitmq-server rabbitmqctl list_queues name messages consumers
```

### Check Connections

```bash
docker exec rabbitmq-server rabbitmqctl list_connections
```

### View Logs

```bash
docker logs -f rabbitmq-server
```

## Common Operations

### Purge a Queue (Delete All Messages)

```bash
docker exec rabbitmq-server rabbitmqctl purge_queue emails.to_classify
```

### Delete a Queue

```bash
docker exec rabbitmq-server rabbitmqctl delete_queue emails.to_classify
```

### List Exchanges

```bash
docker exec rabbitmq-server rabbitmqctl list_exchanges
```

### List Bindings

```bash
docker exec rabbitmq-server rabbitmqctl list_bindings
```

## Troubleshooting

### Issue: "Connection refused"

**Cause**: RabbitMQ not fully started

**Solution**: Wait 30-60 seconds after `docker-compose up`, then retry

```bash
# Check health
docker-compose -f docker-compose.rabbitmq.yml ps
```

### Issue: "Access refused" (401/403)

**Cause**: Incorrect credentials

**Solution**: Verify username/password in `.env` matches Docker Compose

### Issue: "Queue does not exist"

**Cause**: Queue not created yet

**Solution**: Create queue via UI or Python script

### Issue: Messages disappearing

**Cause**: Non-durable queue or non-persistent messages

**Solution**: Ensure:
- Queue declared with `durable=True`
- Messages published with `delivery_mode=2`

### Issue: High memory usage

**Cause**: Messages accumulating in queues

**Solution**: Start consumers to process messages

```bash
# Check memory
docker stats rabbitmq-server
```

## Performance Tuning

### For High Throughput

```python
# Use confirm mode for reliability
channel.confirm_delivery()

# Batch publish
for message in messages:
    channel.basic_publish(...)
```

### For Low Latency

```python
# Use QoS to prefetch messages
channel.basic_qos(prefetch_count=1)

# Process one at a time
channel.basic_consume(queue='emails.to_classify', on_message_callback=callback)
```

### For High Availability

Use RabbitMQ cluster with mirrored queues (see production guide).

## Running the Full Pipeline

### Step 1: Start Consumers

**Terminal 1 - Email Classifier**:
```bash
python -m app.consumers.email_classifier_consumer
```

**Terminal 2 - RAG Generator**:
```bash
python -m app.consumers.rag_response_consumer
```

**Terminal 3 - Email Sender**:
```bash
python -m app.consumers.email_sender_consumer
```

### Step 2: Start Email Poller (Producer)

**Terminal 4**:
```bash
python run.py rabbitmq-producer --poll-interval 60
```

Now emails will flow through the pipeline automatically!

## Cleanup

### Stop RabbitMQ (keep data)

```bash
docker-compose -f docker-compose.rabbitmq.yml stop
```

### Stop and Remove All Data

```bash
docker-compose -f docker-compose.rabbitmq.yml down -v
```

**Warning**: This deletes all messages and queues!

## Next Steps

1. ✅ Verify RabbitMQ is running
2. ✅ Test message publish/consume
3. 📖 Read [RabbitMQ Architecture](../architecture/RABBITMQ_ARCHITECTURE.md)
4. 💻 Implement producer service
5. 💻 Implement consumer services
6. 🚀 Deploy to production

## Useful Resources

- **Management UI**: http://localhost:15672
- **RabbitMQ Docs**: https://www.rabbitmq.com/documentation.html
- **Pika Docs**: https://pika.readthedocs.io/
- **Best Practices**: https://www.rabbitmq.com/best-practices.html

---

**Happy Queuing! 🐰**
