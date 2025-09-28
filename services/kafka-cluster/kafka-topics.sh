#!/bin/bash

# Kafka Topic Management Script
# Create and configure topics for HMS microservices

# Kafka broker address
KAFKA_BROKERS="kafka-1:9092,kafka-2:9092,kafka-3:9092"

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
until docker exec kafka-1 kafka-broker-api-versions --bootstrap-server kafka-1:9092; do
  echo "Waiting for Kafka..."
  sleep 5
done

echo "Kafka is ready. Creating topics..."

# Patient Events
docker exec kafka-1 kafka-topics --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic patient-events \
  --partitions 6 \
  --replication-factor 3 \
  --config cleanup.policy=compact \
  --config retention.ms=604800000 \
  --config segment.bytes=1073741824 \
  --if-not-exists

# Authentication Events
docker exec kafka-1 kafka-topics --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic auth-events \
  --partitions 3 \
  --replication-factor 3 \
  --config cleanup.policy=delete \
  --config retention.ms=2592000000 \
  --config segment.bytes=1073741824 \
  --if-not-exists

# Appointment Events
docker exec kafka-1 kafka-topics --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic appointment-events \
  --partitions 6 \
  --replication-factor 3 \
  --config cleanup.policy=compact \
  --config retention.ms=604800000 \
  --config segment.bytes=1073741824 \
  --if-not-exists

# Clinical Events (EHR)
docker exec kafka-1 kafka-topics --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic clinical-events \
  --partitions 12 \
  --replication-factor 3 \
  --config cleanup.policy=compact \
  --config retention.ms=2592000000 \
  --config segment.bytes=1073741824 \
  --if-not-exists

# Billing Events
docker exec kafka-1 kafka-topics --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic billing-events \
  --partitions 6 \
  --replication-factor 3 \
  --config cleanup.policy=compact \
  --config retention.ms=2592000000 \
  --config segment.bytes=1073741824 \
  --if-not-exists

# Pharmacy Events
docker exec kafka-1 kafka-topics --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic pharmacy-events \
  --partitions 6 \
  --replication-factor 3 \
  --config cleanup.policy=compact \
  --config retention.ms=604800000 \
  --config segment.bytes=1073741824 \
  --if-not-exists

# Laboratory Events
docker exec kafka-1 kafka-topics --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic lab-events \
  --partitions 6 \
  --replication-factor 3 \
  --config cleanup.policy=compact \
  --config retention.ms=604800000 \
  --config segment.bytes=1073741824 \
  --if-not-exists

# Radiology Events
docker exec kafka-1 kafka-topics --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic radiology-events \
  --partitions 6 \
  --replication-factor 3 \
  --config cleanup.policy=compact \
  --config retention.ms=604800000 \
  --config segment.bytes=1073741824 \
  --if-not-exists

# Audit Events
docker exec kafka-1 kafka-topics --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic audit-events \
  --partitions 3 \
  --replication-factor 3 \
  --config cleanup.policy=delete \
  --config retention.ms=31536000000 \
  --config segment.bytes=1073741824 \
  --if-not-exists

# Notification Events
docker exec kafka-1 kafka-topics --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic notification-events \
  --partitions 6 \
  --replication-factor 3 \
  --config cleanup.policy=delete \
  --config retention.ms=604800000 \
  --config segment.bytes=1073741824 \
  --if-not-exists

# Analytics Events
docker exec kafka-1 kafka-topics --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic analytics-events \
  --partitions 12 \
  --replication-factor 3 \
  --config cleanup.policy=delete \
  --config retention.ms=2592000000 \
  --config segment.bytes=1073741824 \
  --if-not-exists

# Integration Events (External Systems)
docker exec kafka-1 kafka-topics --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic integration-events \
  --partitions 6 \
  --replication-factor 3 \
  --config cleanup.policy=compact \
  --config retention.ms=604800000 \
  --config segment.bytes=1073741824 \
  --if-not-exists

# Emergency Events (High Priority)
docker exec kafka-1 kafka-topics --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic emergency-events \
  --partitions 3 \
  --replication-factor 3 \
  --config cleanup.policy=delete \
  --config retention.ms=604800000 \
  --config segment.bytes=1073741824 \
  --config message.timestamp.type=LogAppendTime \
  --if-not-exists

# Dead Letter Queue
docker exec kafka-1 kafka-topics --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic dead-letter-queue \
  --partitions 3 \
  --replication-factor 3 \
  --config cleanup.policy=delete \
  --config retention.ms=604800000 \
  --config segment.bytes=1073741824 \
  --if-not-exists

# Schema Registry Topics
docker exec kafka-1 kafka-topics --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic _schemas \
  --partitions 3 \
  --replication-factor 3 \
  --config cleanup.policy=compact \
  --if-not-exists

# Connect Configuration Topics
docker exec kafka-1 kafka-topics --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic hms-connect-configs \
  --partitions 3 \
  --replication-factor 3 \
  --config cleanup.policy=compact \
  --if-not-exists

docker exec kafka-1 kafka-topics --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic hms-connect-offsets \
  --partitions 25 \
  --replication-factor 3 \
  --config cleanup.policy=compact \
  --if-not-exists

docker exec kafka-1 kafka-topics --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic hms-connect-status \
  --partitions 10 \
  --replication-factor 3 \
  --config cleanup.policy=compact \
  --if-not-exists

# Consumer Offset Topics
docker exec kafka-1 kafka-topics --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic __consumer_offsets \
  --partitions 50 \
  --replication-factor 3 \
  --config cleanup.policy=compact \
  --if-not-exists

# Transaction State Topics
docker exec kafka-1 kafka-topics --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic __transaction_state \
  --partitions 25 \
  --replication-factor 3 \
  --config cleanup.policy=compact \
  --if-not-exists

echo "Topics created successfully!"

# Display topic information
echo -e "\n=== Topic Information ==="
docker exec kafka-1 kafka-topics --list --bootstrap-server $KAFKA_BROKERS | grep -E "(patient|auth|appointment|clinical|billing|pharmacy|lab|radiology|audit|notification|analytics|integration|emergency|dead-letter|_schemas|connect|consumer|transaction)"

echo -e "\n=== Topic Details ==="
for topic in patient-events auth-events appointment-events clinical-events billing-events pharmacy-events lab-events radiology-events audit-events notification-events analytics-events integration-events emergency-events dead-letter-queue; do
  echo -e "\nTopic: $topic"
  docker exec kafka-1 kafka-topics --describe --bootstrap-server $KAFKA_BROKERS --topic $topic
done

echo -e "\n=== Kafka Topics Setup Complete ==="