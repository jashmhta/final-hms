"""
Real-time Data Ingestion Pipeline for AI/ML Healthcare System
Handles streaming patient data for real-time analytics and predictions
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, AsyncGenerator
import pandas as pd
import numpy as np
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import fastavro
import pydantic
from pydantic import BaseModel, Field
import prometheus_client
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
INGESTED_RECORDS = prometheus_client.Counter(
    'hms_data_ingested_records_total',
    'Total number of records ingested',
    ['data_type', 'source']
)

PROCESSING_LATENCY = prometheus_client.Histogram(
    'hms_data_processing_latency_seconds',
    'Data processing latency',
    ['data_type']
)

DATA_QUALITY_SCORE = prometheus_client.Gauge(
    'hms_data_quality_score',
    'Data quality score (0-100)',
    ['data_type']
)

# Data models for validation
class VitalSigns(BaseModel):
    heart_rate: float = Field(..., ge=0, le=300)
    blood_pressure_systolic: float = Field(..., ge=0, le=300)
    blood_pressure_diastolic: float = Field(..., ge=0, le=200)
    oxygen_saturation: float = Field(..., ge=0, le=100)
    temperature: float = Field(..., ge=20, le=45)
    respiratory_rate: float = Field(..., ge=0, le=60)

class LabResult(BaseModel):
    test_name: str
    value: float
    unit: str
    reference_range: str
    is_abnormal: bool = False

class MedicationAdministration(BaseModel):
    medication_name: str
    dosage: str
    route: str
    administration_time: datetime
    administered_by: str

class PatientEvent(BaseModel):
    patient_id: str
    event_type: str
    event_timestamp: datetime
    event_data: dict
    source_system: str

class RealtimeDataIngestor:
    """
    Real-time data ingestion pipeline for healthcare data
    """

    def __init__(self, config: Dict):
        self.config = config
        self.kafka_bootstrap_servers = config['kafka']['bootstrap_servers']
        self.redis_host = config['redis']['host']
        self.redis_port = config['redis']['port']
        self.db_config = config['database']

        # Initialize connections
        self.redis_client = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            decode_responses=True
        )

        # Kafka setup
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=self.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
            acks='all',
            retries=3
        )

        # Data quality rules
        self.quality_rules = {
            'vital_signs': self.validate_vital_signs,
            'lab_results': self.validate_lab_results,
            'medications': self.validate_medications
        }

        # Initialize metrics
        self.initialize_metrics()

    def initialize_metrics(self):
        """Initialize Prometheus metrics"""
        prometheus_client.start_http_server(8000)
        logger.info("Prometheus metrics server started on port 8000")

    async def ingest_patient_data(self, data_stream: AsyncGenerator[Dict, None]):
        """
        Main ingestion pipeline for patient data

        Args:
            data_stream: Async generator of patient data
        """
        async for data in data_stream:
            start_time = time.time()

            try:
                # Validate and preprocess data
                validated_data = await self.validate_and_preprocess(data)

                # Check data quality
                quality_score = self.assess_data_quality(validated_data)
                DATA_QUALITY_SCORE.labels(data_type=validated_data['type']).set(quality_score)

                if quality_score < 70:
                    logger.warning(f"Low data quality score: {quality_score} for {validated_data['type']}")
                    # Send to data quality issue queue
                    await self.send_to_quality_issue_queue(validated_data)

                # Enrich data
                enriched_data = await self.enrich_data(validated_data)

                # Store in real-time cache (Redis)
                await self.store_in_cache(enriched_data)

                # Send to Kafka for downstream processing
                await self.send_to_kafka(enriched_data)

                # Update metrics
                INGESTED_RECORDS.labels(
                    data_type=enriched_data['type'],
                    source=enriched_data.get('source', 'unknown')
                ).inc()

                PROCESSING_LATENCY.labels(data_type=enriched_data['type']).observe(
                    time.time() - start_time
                )

                logger.info(f"Successfully ingested {enriched_data['type']} data for patient {enriched_data['patient_id']}")

            except Exception as e:
                logger.error(f"Error ingesting data: {e}")
                # Send to error queue for retry
                await self.handle_ingestion_error(data, e)

    async def validate_and_preprocess(self, raw_data: Dict) -> Dict:
        """
        Validate and preprocess incoming data

        Args:
            raw_data: Raw data from source

        Returns:
            Validated and preprocessed data
        """
        data_type = raw_data.get('type')

        if data_type == 'vital_signs':
            # Validate using Pydantic model
            vital_signs = VitalSigns(**raw_data['data'])
            processed_data = {
                'patient_id': raw_data['patient_id'],
                'type': 'vital_signs',
                'timestamp': raw_data.get('timestamp', datetime.utcnow()),
                'data': vital_signs.dict(),
                'source': raw_data.get('source', 'unknown'),
                'quality_score': 100
            }

        elif data_type == 'lab_results':
            lab_result = LabResult(**raw_data['data'])
            # Check if value is within reference range
            is_abnormal = self.check_lab_result_abnormal(lab_result)
            lab_result.is_abnormal = is_abnormal

            processed_data = {
                'patient_id': raw_data['patient_id'],
                'type': 'lab_results',
                'timestamp': raw_data.get('timestamp', datetime.utcnow()),
                'data': lab_result.dict(),
                'source': raw_data.get('source', 'unknown'),
                'quality_score': 100
            }

        elif data_type == 'medication_administration':
            med_admin = MedicationAdministration(**raw_data['data'])
            processed_data = {
                'patient_id': raw_data['patient_id'],
                'type': 'medication_administration',
                'timestamp': raw_data.get('timestamp', datetime.utcnow()),
                'data': med_admin.dict(),
                'source': raw_data.get('source', 'unknown'),
                'quality_score': 100
            }

        else:
            # Generic event processing
            event = PatientEvent(**raw_data)
            processed_data = {
                'patient_id': event.patient_id,
                'type': event.event_type,
                'timestamp': event.event_timestamp,
                'data': event.event_data,
                'source': event.source_system,
                'quality_score': 100
            }

        return processed_data

    def validate_vital_signs(self, vital_signs: Dict) -> bool:
        """Validate vital signs data"""
        try:
            vs = VitalSigns(**vital_signs)
            return True
        except pydantic.ValidationError:
            return False

    def validate_lab_results(self, lab_result: Dict) -> bool:
        """Validate lab result data"""
        try:
            lr = LabResult(**lab_result)
            return True
        except pydantic.ValidationError:
            return False

    def validate_medications(self, medication: Dict) -> bool:
        """Validate medication administration data"""
        try:
            ma = MedicationAdministration(**medication)
            return True
        except pydantic.ValidationError:
            return False

    def check_lab_result_abnormal(self, lab_result: LabResult) -> bool:
        """
        Check if lab result is abnormal based on reference range

        Args:
            lab_result: Lab result object

        Returns:
            Boolean indicating if result is abnormal
        """
        try:
            # Parse reference range (e.g., "3.5-5.0", "<150", ">0.5")
            ref_range = lab_result.reference_range

            if '-' in ref_range:
                # Range format (e.g., "3.5-5.0")
                min_val, max_val = map(float, ref_range.split('-'))
                return lab_result.value < min_val or lab_result.value > max_val
            elif ref_range.startswith('<'):
                # Less than format (e.g., "<150")
                max_val = float(ref_range[1:])
                return lab_result.value >= max_val
            elif ref_range.startswith('>'):
                # Greater than format (e.g., ">0.5")
                min_val = float(ref_range[1:])
                return lab_result.value <= min_val
            else:
                # Unknown format, assume normal
                return False

        except Exception:
            return False

    def assess_data_quality(self, data: Dict) -> float:
        """
        Assess data quality score (0-100)

        Args:
            data: Validated data

        Returns:
            Quality score
        """
        score = 100
        deductions = 0

        # Check for missing required fields
        required_fields = ['patient_id', 'type', 'timestamp', 'data']
        for field in required_fields:
            if field not in data or data[field] is None:
                deductions += 20

        # Check timestamp recency
        timestamp = data.get('timestamp')
        if timestamp:
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

            time_diff = datetime.utcnow() - timestamp
            if time_diff > timedelta(hours=24):
                deductions += 10
            elif time_diff > timedelta(hours=1):
                deductions += 5

        # Type-specific quality checks
        data_type = data.get('type')
        if data_type in self.quality_rules:
            if not self.quality_rules[data_type](data['data']):
                deductions += 30

        return max(0, score - deductions)

    async def enrich_data(self, data: Dict) -> Dict:
        """
        Enrich data with additional context

        Args:
            data: Validated data

        Returns:
            Enriched data
        """
        patient_id = data['patient_id']

        # Get patient context from cache or database
        patient_context = await self.get_patient_context(patient_id)

        # Add enrichment
        enriched_data = data.copy()
        enriched_data['enrichment'] = {
            'patient_age': patient_context.get('age'),
            'patient_gender': patient_context.get('gender'),
            'admission_status': patient_context.get('admission_status'),
            'current_ward': patient_context.get('ward'),
            'attending_physician': patient_context.get('attending_physician'),
            'enrichment_timestamp': datetime.utcnow().isoformat()
        }

        # Add risk scores if available
        risk_scores = await self.get_patient_risk_scores(patient_id)
        if risk_scores:
            enriched_data['risk_scores'] = risk_scores

        return enriched_data

    async def get_patient_context(self, patient_id: str) -> Dict:
        """Get patient context from cache or database"""
        # Try Redis first
        cache_key = f"patient_context:{patient_id}"
        cached_data = self.redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        # Fetch from database if not in cache
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = """
                SELECT age, gender, admission_status, ward, attending_physician
                FROM patients
                WHERE patient_id = %s
            """
            cursor.execute(query, (patient_id,))
            result = cursor.fetchone()

            if result:
                # Cache for 5 minutes
                self.redis_client.setex(
                    cache_key,
                    300,
                    json.dumps(dict(result), default=str)
                )
                return dict(result)

        except Exception as e:
            logger.error(f"Error fetching patient context: {e}")

        return {}

    async def get_patient_risk_scores(self, patient_id: str) -> Optional[Dict]:
        """Get current risk scores for patient"""
        cache_key = f"risk_scores:{patient_id}"
        cached_scores = self.redis_client.get(cache_key)

        if cached_scores:
            return json.loads(cached_scores)

        return None

    async def store_in_cache(self, data: Dict):
        """Store data in Redis cache"""
        patient_id = data['patient_id']
        data_type = data['type']

        # Store in patient timeline
        timeline_key = f"patient_timeline:{patient_id}"
        timeline_entry = {
            'type': data_type,
            'timestamp': data['timestamp'].isoformat(),
            'data': data['data']
        }

        # Add to sorted set with timestamp as score
        self.redis_client.zadd(
            timeline_key,
            {json.dumps(timeline_entry): datetime.utcnow().timestamp()}
        )

        # Keep only last 1000 entries
        self.redis_client.zremrangebyrank(timeline_key, 0, -1001)

        # Store latest data by type
        latest_key = f"latest_{data_type}:{patient_id}"
        self.redis_client.setex(
            latest_key,
            3600,  # 1 hour TTL
            json.dumps(data, default=str)
        )

    async def send_to_kafka(self, data: Dict):
        """Send data to Kafka topic"""
        topic = f"hms_{data['type']}"

        try:
            self.kafka_producer.send(
                topic,
                value=data,
                key=data['patient_id'].encode('utf-8')
            )
            self.kafka_producer.flush()
        except KafkaError as e:
            logger.error(f"Error sending to Kafka: {e}")
            raise

    async def send_to_quality_issue_queue(self, data: Dict):
        """Send low-quality data to quality issue queue"""
        quality_issue = {
            'original_data': data,
            'issue_type': 'low_quality',
            'timestamp': datetime.utcnow().isoformat(),
            'retry_count': 0
        }

        self.kafka_producer.send(
            'hms_data_quality_issues',
            value=quality_issue
        )

    async def handle_ingestion_error(self, data: Dict, error: Exception):
        """Handle ingestion errors"""
        error_record = {
            'original_data': data,
            'error': str(error),
            'timestamp': datetime.utcnow().isoformat(),
            'retry_count': 0
        }

        self.kafka_producer.send(
            'hms_ingestion_errors',
            value=error_record
        )

    async def create_stream_processing_pipeline(self):
        """Create Apache Beam pipeline for batch processing"""
        options = PipelineOptions([
            '--runner=DirectRunner',
            '--job_name=hms-data-processing'
        ])

        with beam.Pipeline(options=options) as p:
            # Read from Kafka
            (p
             | 'ReadFromKafka' >> beam.io.ReadFromKafka(
                 consumer_config={
                     'bootstrap.servers': self.kafka_bootstrap_servers,
                     'group.id': 'hms-data-processor',
                     'auto.offset.reset': 'earliest'
                 },
                 topics=['hms_vital_signs', 'hms_lab_results']
             )
             | 'DecodeMessages' >> beam.Map(lambda msg: json.loads(msg.value.decode('utf-8')))
             | 'ProcessData' >> beam.ParDo(ProcessDataFn())
             | 'WriteToBigQuery' >> beam.io.WriteToBigQuery(
                 table='hms_analytics.processed_data',
                 schema='patient_id:STRING,timestamp:TIMESTAMP,data_type:STRING,data:JSON'
             ))

    async def start_consumer(self, topics: List[str]):
        """Start Kafka consumer for real-time processing"""
        consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=self.kafka_bootstrap_servers,
            group_id='hms-ai-processor',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest'
        )

        logger.info(f"Started consumer for topics: {topics}")

        for message in consumer:
            try:
                # Process message for real-time AI predictions
                await self.process_realtime_message(message.value)
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    async def process_realtime_message(self, message: Dict):
        """Process individual message for real-time AI"""
        # This would integrate with AI models for real-time predictions
        patient_id = message['patient_id']
        data_type = message['type']

        # Trigger appropriate AI predictions based on data type
        if data_type == 'vital_signs':
            await self.trigger_vital_signs_analysis(patient_id, message['data'])
        elif data_type == 'lab_results':
            await self.trigger_lab_analysis(patient_id, message['data'])

    async def trigger_vital_signs_analysis(self, patient_id: str, vital_signs: Dict):
        """Trigger AI analysis of vital signs"""
        # Check for sepsis risk
        sepsis_score = self.calculate_sepsis_score(vital_signs)
        if sepsis_score > 5:
            # Send sepsis alert
            alert = {
                'patient_id': patient_id,
                'alert_type': 'sepsis_risk',
                'severity': 'high' if sepsis_score > 7 else 'medium',
                'score': sepsis_score,
                'timestamp': datetime.utcnow().isoformat()
            }
            await self.send_alert(alert)

    async def trigger_lab_analysis(self, patient_id: str, lab_result: Dict):
        """Trigger AI analysis of lab results"""
        # Check for critical values
        if lab_result.get('is_abnormal', False):
            alert = {
                'patient_id': patient_id,
                'alert_type': 'abnormal_lab_value',
                'severity': 'high',
                'test_name': lab_result['test_name'],
                'value': lab_result['value'],
                'reference_range': lab_result['reference_range'],
                'timestamp': datetime.utcnow().isoformat()
            }
            await self.send_alert(alert)

    def calculate_sepsis_score(self, vital_signs: Dict) -> float:
        """Calculate sepsis risk score based on vital signs"""
        score = 0

        # Heart rate
        if vital_signs['heart_rate'] > 90:
            score += 1

        # Respiratory rate
        if vital_signs['respiratory_rate'] > 20:
            score += 1

        # Temperature
        if vital_signs['temperature'] > 38 or vital_signs['temperature'] < 36:
            score += 1

        # Oxygen saturation
        if vital_signs['oxygen_saturation'] < 95:
            score += 2

        return score

    async def send_alert(self, alert: Dict):
        """Send clinical alert"""
        self.kafka_producer.send(
            'hms_clinical_alerts',
            value=alert
        )
        logger.warning(f"Alert sent: {alert}")


class ProcessDataFn(beam.DoFn):
    """Apache Beam processing function"""

    def process(self, element):
        # Process data element
        processed = {
            'patient_id': element['patient_id'],
            'timestamp': element['timestamp'],
            'data_type': element['type'],
            'data': json.dumps(element['data'])
        }
        yield processed


# Example usage
if __name__ == "__main__":
    # Configuration
    config = {
        'kafka': {
            'bootstrap_servers': 'localhost:9092'
        },
        'redis': {
            'host': 'localhost',
            'port': 6379
        },
        'database': {
            'host': 'localhost',
            'database': 'hms',
            'user': 'hms_user',
            'password': 'password'
        }
    }

    # Initialize ingestor
    ingestor = RealtimeDataIngestor(config)

    # Example data stream
    async def sample_data_stream():
        sample_data = [
            {
                'patient_id': 'P12345',
                'type': 'vital_signs',
                'timestamp': datetime.utcnow(),
                'data': {
                    'heart_rate': 85,
                    'blood_pressure_systolic': 120,
                    'blood_pressure_diastolic': 80,
                    'oxygen_saturation': 98,
                    'temperature': 36.8,
                    'respiratory_rate': 16
                },
                'source': 'monitoring_device'
            }
        ]
        for data in sample_data:
            yield data
            await asyncio.sleep(1)

    # Run ingestion
    asyncio.run(ingestor.ingest_patient_data(sample_data_stream()))