# Kafka and Zookeeper Quick Start Guide

This guide will help you get started with the Kafka and Zookeeper implementation for local development and testing.

## Prerequisites

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Python**: 3.12+ (for running consumers)
- **Memory**: At least 8 GB RAM available for Docker

## Quick Start

### 1. Start Kafka Cluster

Start the Kafka and Zookeeper cluster using Docker Compose:

```bash
# From the project root
docker-compose -f docker-compose.kafka.yml up -d

# Wait for all services to be healthy (30-60 seconds)
docker-compose -f docker-compose.kafka.yml ps
```

**Expected output:**
```
NAME                STATUS              PORTS
kafka-broker-1      Up (healthy)        0.0.0.0:9092->9092/tcp, 0.0.0.0:19092->19092/tcp
kafka-broker-2      Up (healthy)        0.0.0.0:9093->9093/tcp, 0.0.0.0:19093->19093/tcp
kafka-broker-3      Up (healthy)        0.0.0.0:9094->9094/tcp, 0.0.0.0:19094->19094/tcp
zookeeper-1         Up                  0.0.0.0:2181->2181/tcp
zookeeper-2         Up                  0.0.0.0:2182->2181/tcp
zookeeper-3         Up                  0.0.0.0:2183->2181/tcp
kafdrop             Up                  0.0.0.0:9000->9000/tcp
redis-cache         Up                  0.0.0.0:6379->6379/tcp
```

### 2. Access Kafdrop UI

Open your browser and navigate to:

```
http://localhost:9000
```

You should see the Kafdrop interface showing all Kafka topics and brokers.

### 3. Verify Topics Created

Check that all topics were created successfully:

```bash
docker exec -it kafka-broker-1 kafka-topics \
  --bootstrap-server localhost:9092 \
  --list
```

**Expected output:**
```
dlq.failed-events
documents.to-ingest
emails.classified
emails.incoming
emails.response-ready
events.email-sent
```

### 4. Install Python Dependencies

Install the Kafka client library:

```bash
pip install kafka-python redis
```

### 5. Configure Environment

Add Kafka configuration to your `.env` file:

```env
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:19092,localhost:19093,localhost:19094
KAFKA_ENABLED=true

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Testing the Setup

### Test 1: Produce a Test Message

Create a simple producer script to test publishing:

```python
# test_producer.py
from kafka import KafkaProducer
import json
from datetime import datetime
import uuid

producer = KafkaProducer(
    bootstrap_servers=['localhost:19092', 'localhost:19093', 'localhost:19094'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Test email event
test_event = {
    "event_id": str(uuid.uuid4()),
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "email_id": "test-email-123",
    "thread_id": "test-thread-456",
    "from": "test@example.com",
    "to": "support@company.com",
    "subject": "Test Email",
    "body": "This is a test email for Kafka integration",
    "agent_email": "support@company.com"
}

# Publish to emails.incoming topic
future = producer.send('emails.incoming', value=test_event)
result = future.get(timeout=10)

print(f"✅ Message published to partition {result.partition} at offset {result.offset}")
producer.close()
```

Run the test:

```bash
python test_producer.py
```

### Test 2: Consume the Test Message

Create a simple consumer to verify message receipt:

```python
# test_consumer.py
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'emails.incoming',
    bootstrap_servers=['localhost:19092', 'localhost:19093', 'localhost:19094'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    group_id='test-consumer-group'
)

print("🔍 Waiting for messages...")

for message in consumer:
    event = message.value
    print(f"\n✅ Received message:")
    print(f"   Event ID: {event['event_id']}")
    print(f"   From: {event['from']}")
    print(f"   Subject: {event['subject']}")
    print(f"   Partition: {message.partition}")
    print(f"   Offset: {message.offset}")
    break

consumer.close()
```

Run the test:

```bash
python test_consumer.py
```

## Monitoring Consumer Lag

Check consumer group lag to ensure consumers are keeping up:

```bash
docker exec -it kafka-broker-1 kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group test-consumer-group
```

**Example output:**
```
GROUP              TOPIC            PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
test-consumer-group emails.incoming  0          1               1               0
test-consumer-group emails.incoming  1          0               0               0
...
```

**LAG = 0** means the consumer is fully caught up.

## Running the Full Pipeline

### Step 1: Start Email Classifier Consumer

```bash
# From project root
python -m app.consumers.email_classifier
```

### Step 2: Start RAG Response Generator Consumer

```bash
# In another terminal
python -m app.consumers.rag_response_generator
```

### Step 3: Start Email Sender Consumer

```bash
# In another terminal
python -m app.consumers.email_sender
```

### Step 4: Start Email Poller (Producer)

```bash
# In another terminal
python run.py kafka-producer --poll-interval 60
```

## Troubleshooting

### Issue: "Connection refused" errors

**Cause**: Kafka brokers not fully started

**Solution**: Wait 60 seconds after starting Docker Compose, then retry

```bash
# Check broker health
docker-compose -f docker-compose.kafka.yml ps
```

### Issue: Topics not appearing in Kafdrop

**Cause**: Topic initialization failed

**Solution**: Manually create topics

```bash
docker exec -it kafka-broker-1 kafka-topics \
  --create --if-not-exists \
  --bootstrap-server localhost:9092 \
  --topic emails.incoming \
  --partitions 12 \
  --replication-factor 3
```

### Issue: Consumer lag increasing

**Cause**: Consumers processing too slowly

**Solution**: Scale up consumer instances

```bash
# Start additional classifier consumers
python -m app.consumers.email_classifier &
python -m app.consumers.email_classifier &
```

### Issue: "Not enough replicas" errors

**Cause**: Less than 3 brokers available

**Solution**: Ensure all 3 brokers are healthy

```bash
docker-compose -f docker-compose.kafka.yml restart kafka-broker-1 kafka-broker-2 kafka-broker-3
```

## Performance Tuning

### For High Throughput

Adjust consumer configuration:

```python
consumer = KafkaConsumer(
    'emails.incoming',
    bootstrap_servers=bootstrap_servers,
    max_poll_records=50,  # Increase batch size
    fetch_min_bytes=1024,  # Wait for more data
    fetch_max_wait_ms=500  # Max wait time
)
```

### For Low Latency

```python
consumer = KafkaConsumer(
    'emails.incoming',
    bootstrap_servers=bootstrap_servers,
    max_poll_records=10,  # Smaller batches
    fetch_min_bytes=1,  # Don't wait
    fetch_max_wait_ms=100  # Lower wait time
)
```

## Cleanup

### Stop all services but keep data

```bash
docker-compose -f docker-compose.kafka.yml stop
```

### Stop and remove all data (WARNING: Deletes all messages)

```bash
docker-compose -f docker-compose.kafka.yml down -v
```

### Remove only Kafka data (keep topics but delete messages)

```bash
docker volume rm rag-demo_kafka-broker-1-data
docker volume rm rag-demo_kafka-broker-2-data
docker volume rm rag-demo_kafka-broker-3-data
```

## Next Steps

1. **Implement producers**: Integrate `KafkaProducerService` into existing code
2. **Deploy consumers**: Set up consumer services as separate processes
3. **Add monitoring**: Integrate Prometheus metrics for observability
4. **Load testing**: Test with high email volumes
5. **Production deployment**: Deploy to Kubernetes using provided manifests

## Useful Commands

### View topic configuration

```bash
docker exec -it kafka-broker-1 kafka-topics \
  --bootstrap-server localhost:9092 \
  --describe \
  --topic emails.incoming
```

### Delete a topic (development only)

```bash
docker exec -it kafka-broker-1 kafka-topics \
  --bootstrap-server localhost:9092 \
  --delete \
  --topic emails.incoming
```

### Check Zookeeper status

```bash
docker exec -it zookeeper-1 zkServer.sh status
```

### View broker logs

```bash
docker logs -f kafka-broker-1
```

### Reset consumer group offset (reprocess all messages)

```bash
docker exec -it kafka-broker-1 kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group email-classifier-group \
  --reset-offsets \
  --to-earliest \
  --topic emails.incoming \
  --execute
```

## Resources

- **Kafdrop UI**: http://localhost:9000
- **Kafka Documentation**: https://kafka.apache.org/documentation/
- **Confluent Platform Docs**: https://docs.confluent.io/platform/current/
- **kafka-python Docs**: https://kafka-python.readthedocs.io/

---

**Happy Streaming! 🚀**
