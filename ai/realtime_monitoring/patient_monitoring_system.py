"""
Real-time Patient Monitoring and Alert System
Provides continuous monitoring of patient vital signs and clinical parameters
with AI-powered early warning and intervention recommendations
"""

import asyncio
import json
import logging
import smtplib
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import AsyncGenerator, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import prometheus_client
import redis
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from jinja2 import Template
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
PATIENTS_MONITORED = prometheus_client.Gauge(
    "hms_patients_monitored_total", "Total number of patients being monitored"
)

ALERTS_GENERATED = prometheus_client.Counter(
    "hms_alerts_generated_total", "Total alerts generated", ["alert_type", "severity"]
)

MONITORING_LATENCY = prometheus_client.Histogram(
    "hms_monitoring_latency_seconds", "Patient monitoring processing latency"
)

EARLY_WARNING_SCORES = prometheus_client.Gauge(
    "hms_early_warning_scores",
    "Early warning scores for monitored patients",
    ["patient_id", "score_type"],
)


# Pydantic models
class VitalSigns(BaseModel):
    timestamp: datetime
    heart_rate: Optional[float] = Field(None, ge=0, le=300)
    blood_pressure_systolic: Optional[float] = Field(None, ge=0, le=300)
    blood_pressure_diastolic: Optional[float] = Field(None, ge=0, le=200)
    oxygen_saturation: Optional[float] = Field(None, ge=0, le=100)
    temperature: Optional[float] = Field(None, ge=20, le=45)
    respiratory_rate: Optional[float] = Field(None, ge=0, le=60)
    consciousness_level: Optional[str] = (
        None  # 'alert', 'voice', 'pain', 'unresponsive'
    )


class PatientAlert(BaseModel):
    patient_id: str
    alert_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    score: float
    triggered_by: List[str]
    timestamp: datetime
    message: str
    recommendations: List[str]
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_time: Optional[datetime] = None
    resolved_time: Optional[datetime] = None


class MonitoringConfig(BaseModel):
    patient_id: str
    monitoring_level: str  # 'basic', 'intermediate', 'intensive'
    alert_thresholds: Dict[str, Dict[str, float]]
    monitoring_intervals: Dict[str, int]  # seconds
    escalation_contacts: List[Dict]
    custom_rules: Optional[List[Dict]] = None


@dataclass
class PatientMonitoringState:
    """State tracking for a monitored patient"""

    patient_id: str
    vital_signs_history: List[VitalSigns]
    current_ews_score: float
    alert_history: List[PatientAlert]
    last_update: datetime
    monitoring_config: MonitoringConfig
    trend_data: Dict[str, List[float]]  # For trend analysis


class ConnectionManager:
    """Manages WebSocket connections for real-time alerts"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Connection might be closed
                pass


class RealtimePatientMonitoringSystem:
    """
    Advanced real-time patient monitoring system with AI-powered alerts
    """

    def __init__(self, config: Dict):
        self.config = config
        self.redis_host = config["redis"]["host"]
        self.redis_port = config["redis"]["port"]
        self.db_config = config["database"]
        self.email_config = config.get("email", {})

        # Initialize Redis
        self.redis_client = redis.Redis(
            host=self.redis_host, port=self.redis_port, decode_responses=True
        )

        # Initialize connection manager
        self.connection_manager = ConnectionManager()

        # Patient monitoring states
        self.monitored_patients: Dict[str, PatientMonitoringState] = {}

        # Alert severity colors
        self.severity_colors = {
            "low": "green",
            "medium": "yellow",
            "high": "orange",
            "critical": "red",
        }

        # Alert thresholds
        self.default_thresholds = {
            "heart_rate": {"min": 60, "max": 100},
            "blood_pressure_systolic": {"min": 90, "max": 140},
            "blood_pressure_diastolic": {"min": 60, "max": 90},
            "oxygen_saturation": {"min": 95, "max": 100},
            "temperature": {"min": 36.1, "max": 37.2},
            "respiratory_rate": {"min": 12, "max": 20},
        }

        # Initialize monitoring
        self.start_background_tasks()

    def start_background_tasks(self):
        """Start background monitoring tasks"""
        asyncio.create_task(self.monitor_patients())
        asyncio.create_task(self.check_system_health())
        asyncio.create_task(self.cleanup_old_data())

    async def add_patient_to_monitoring(self, config: MonitoringConfig):
        """Add patient to monitoring system"""
        patient_id = config.patient_id

        # Initialize monitoring state
        monitoring_state = PatientMonitoringState(
            patient_id=patient_id,
            vital_signs_history=[],
            current_ews_score=0,
            alert_history=[],
            last_update=datetime.utcnow(),
            monitoring_config=config,
            trend_data={
                "heart_rate": [],
                "blood_pressure_systolic": [],
                "oxygen_saturation": [],
                "temperature": [],
                "respiratory_rate": [],
            },
        )

        self.monitored_patients[patient_id] = monitoring_state

        # Store in Redis
        await self.store_monitoring_state(patient_id, monitoring_state)

        # Update metrics
        PATIENTS_MONITORED.set(len(self.monitored_patients))

        logger.info(f"Added patient {patient_id} to monitoring")

    async def update_vital_signs(self, patient_id: str, vital_signs: VitalSigns):
        """Update patient vital signs and trigger analysis"""
        start_time = time.time()

        if patient_id not in self.monitored_patients:
            logger.warning(f"Patient {patient_id} not in monitoring system")
            return

        # Get monitoring state
        state = self.monitored_patients[patient_id]

        # Add to history
        state.vital_signs_history.append(vital_signs)

        # Keep only last 100 readings
        if len(state.vital_signs_history) > 100:
            state.vital_signs_history = state.vital_signs_history[-100:]

        # Update trend data
        self.update_trend_data(state, vital_signs)

        # Calculate Early Warning Score
        ews_score = self.calculate_ews_score(vital_signs)
        state.current_ews_score = ews_score

        # Update Prometheus metrics
        EARLY_WARNING_SCORES.labels(patient_id=patient_id, score_type="ews").set(
            ews_score
        )
        MONITORING_LATENCY.observe(time.time() - start_time)

        # Check for alerts
        alerts = await self.check_for_alerts(state, vital_signs, ews_score)

        # Store updated state
        await self.store_monitoring_state(patient_id, state)

        # Broadcast updates if there are alerts
        if alerts:
            for alert in alerts:
                await self.handle_alert(alert)

        # Broadcast vital signs update
        update_message = {
            "type": "vital_signs_update",
            "patient_id": patient_id,
            "vital_signs": vital_signs.dict(),
            "ews_score": ews_score,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.connection_manager.broadcast(json.dumps(update_message))

    def update_trend_data(self, state: PatientMonitoringState, vital_signs: VitalSigns):
        """Update trend data for analysis"""
        for param in [
            "heart_rate",
            "blood_pressure_systolic",
            "oxygen_saturation",
            "temperature",
            "respiratory_rate",
        ]:
            value = getattr(vital_signs, param)
            if value is not None:
                state.trend_data[param].append(value)
                # Keep only last 50 values for trend analysis
                if len(state.trend_data[param]) > 50:
                    state.trend_data[param] = state.trend_data[param][-50:]

    def calculate_ews_score(self, vital_signs: VitalSigns) -> float:
        """
        Calculate Modified Early Warning Score (MEWS)

        Scoring:
        - Heart Rate: <40 (3), 40-50 (1), 51-100 (0), 101-110 (1), 111-130 (2), >130 (3)
        - Systolic BP: <70 (3), 70-80 (2), 81-100 (1), 101-199 (0), >200 (2)
        - Respiratory Rate: <9 (3), 9-14 (0), 15-20 (1), 21-29 (2), >30 (3)
        - Temperature: <35 (2), 35-38.4 (0), >38.5 (2)
        - Consciousness: Alert (0), Voice (1), Pain (2), Unresponsive (3)
        """
        score = 0

        # Heart Rate
        hr = vital_signs.heart_rate
        if hr is not None:
            if hr < 40:
                score += 3
            elif 40 <= hr <= 50:
                score += 1
            elif 51 <= hr <= 100:
                score += 0
            elif 101 <= hr <= 110:
                score += 1
            elif 111 <= hr <= 130:
                score += 2
            elif hr > 130:
                score += 3

        # Systolic Blood Pressure
        sbp = vital_signs.blood_pressure_systolic
        if sbp is not None:
            if sbp < 70:
                score += 3
            elif 70 <= sbp <= 80:
                score += 2
            elif 81 <= sbp <= 100:
                score += 1
            elif 101 <= sbp <= 199:
                score += 0
            elif sbp > 200:
                score += 2

        # Respiratory Rate
        rr = vital_signs.respiratory_rate
        if rr is not None:
            if rr < 9:
                score += 3
            elif 9 <= rr <= 14:
                score += 0
            elif 15 <= rr <= 20:
                score += 1
            elif 21 <= rr <= 29:
                score += 2
            elif rr > 30:
                score += 3

        # Temperature
        temp = vital_signs.temperature
        if temp is not None:
            if temp < 35:
                score += 2
            elif 35 <= temp <= 38.4:
                score += 0
            elif temp > 38.5:
                score += 2

        # Consciousness Level
        if vital_signs.consciousness_level:
            level = vital_signs.consciousness_level.lower()
            if level == "alert":
                score += 0
            elif level == "voice":
                score += 1
            elif level == "pain":
                score += 2
            elif level == "unresponsive":
                score += 3

        return score

    async def check_for_alerts(
        self, state: PatientMonitoringState, vital_signs: VitalSigns, ews_score: float
    ) -> List[PatientAlert]:
        """Check for alert conditions"""
        alerts = []

        # Check EWS score thresholds
        if ews_score >= 5:
            severity = (
                "critical" if ews_score >= 7 else "high" if ews_score >= 6 else "medium"
            )
            alert = PatientAlert(
                patient_id=state.patient_id,
                alert_type="high_ews_score",
                severity=severity,
                score=ews_score,
                triggered_by=["ews_score"],
                timestamp=datetime.utcnow(),
                message=f"Early Warning Score elevated: {ews_score}",
                recommendations=self.get_ews_recommendations(ews_score),
            )
            alerts.append(alert)

        # Check individual vital signs
        thresholds = state.monitoring_config.alert_thresholds or self.default_thresholds

        for param, limits in thresholds.items():
            value = getattr(vital_signs, param)
            if value is not None:
                if value < limits["min"] or value > limits["max"]:
                    severity = self.calculate_vital_sign_severity(param, value, limits)
                    alert = PatientAlert(
                        patient_id=state.patient_id,
                        alert_type=f"{param}_abnormal",
                        severity=severity,
                        score=self.calculate_vital_sign_score(param, value, limits),
                        triggered_by=[param],
                        timestamp=datetime.utcnow(),
                        message=f"{param.replace('_', ' ').title()} abnormal: {value}",
                        recommendations=self.get_vital_sign_recommendations(
                            param, value, severity
                        ),
                    )
                    alerts.append(alert)

        # Check trends
        trend_alerts = self.check_trends(state)
        alerts.extend(trend_alerts)

        # Check custom rules
        if state.monitoring_config.custom_rules:
            custom_alerts = await self.check_custom_rules(state, vital_signs)
            alerts.extend(custom_alerts)

        # Add alerts to history
        for alert in alerts:
            state.alert_history.append(alert)
            ALERTS_GENERATED.labels(
                alert_type=alert.alert_type, severity=alert.severity
            ).inc()

        return alerts

    def calculate_vital_sign_severity(
        self, param: str, value: float, limits: Dict[str, float]
    ) -> str:
        """Calculate severity level for abnormal vital sign"""
        min_val, max_val = limits["min"], limits["max"]

        if param in ["heart_rate", "blood_pressure_systolic", "respiratory_rate"]:
            deviation = max(abs(value - min_val), abs(value - max_val))
            if deviation > 50:
                return "critical"
            elif deviation > 30:
                return "high"
            elif deviation > 15:
                return "medium"
            else:
                return "low"

        elif param == "oxygen_saturation":
            if value < 90:
                return "critical"
            elif value < 93:
                return "high"
            elif value < 95:
                return "medium"
            else:
                return "low"

        elif param == "temperature":
            if value < 34 or value > 40:
                return "critical"
            elif value < 35 or value > 39:
                return "high"
            elif value < 36 or value > 38.5:
                return "medium"
            else:
                return "low"

        return "medium"

    def calculate_vital_sign_score(
        self, param: str, value: float, limits: Dict[str, float]
    ) -> float:
        """Calculate score for abnormal vital sign"""
        min_val, max_val = limits["min"], limits["max"]

        if value < min_val:
            return (min_val - value) / min_val * 10
        elif value > max_val:
            return (value - max_val) / max_val * 10
        return 0

    def check_trends(self, state: PatientMonitoringState) -> List[PatientAlert]:
        """Check for concerning trends in vital signs"""
        alerts = []

        for param, values in state.trend_data.items():
            if len(values) >= 5:
                # Simple trend detection
                recent_values = values[-5:]
                trend = np.polyfit(range(len(recent_values)), recent_values, 1)[0]

                # Check for concerning trends
                if param == "heart_rate" and trend > 5:
                    alert = PatientAlert(
                        patient_id=state.patient_id,
                        alert_type=f"{param}_trend_up",
                        severity="high",
                        score=abs(trend),
                        triggered_by=[f"{param}_trend"],
                        timestamp=datetime.utcnow(),
                        message=f"Heart rate trending upward: {trend:.1f} beats/min increase",
                        recommendations=[
                            "Check for pain, anxiety, or clinical deterioration"
                        ],
                    )
                    alerts.append(alert)

                elif param == "oxygen_saturation" and trend < -2:
                    alert = PatientAlert(
                        patient_id=state.patient_id,
                        alert_type=f"{param}_trend_down",
                        severity="high",
                        score=abs(trend),
                        triggered_by=[f"{param}_trend"],
                        timestamp=datetime.utcnow(),
                        message=f"Oxygen saturation trending downward: {trend:.1f}% decrease",
                        recommendations=[
                            "Check respiratory status, consider oxygen therapy"
                        ],
                    )
                    alerts.append(alert)

        return alerts

    async def check_custom_rules(
        self, state: PatientMonitoringState, vital_signs: VitalSigns
    ) -> List[PatientAlert]:
        """Check custom alert rules"""
        alerts = []

        for rule in state.monitoring_config.custom_rules or []:
            # This is a simplified rule engine
            # In production, you'd use a more sophisticated rule engine
            if self.evaluate_rule(rule, vital_signs, state):
                alert = PatientAlert(
                    patient_id=state.patient_id,
                    alert_type=rule["name"],
                    severity=rule["severity"],
                    score=rule.get("score", 5),
                    triggered_by=rule.get("triggered_by", ["custom_rule"]),
                    timestamp=datetime.utcnow(),
                    message=rule["message"],
                    recommendations=rule.get("recommendations", []),
                )
                alerts.append(alert)

        return alerts

    def evaluate_rule(
        self, rule: Dict, vital_signs: VitalSigns, state: PatientMonitoringState
    ) -> bool:
        """Evaluate a custom rule"""
        # Simplified rule evaluation
        conditions = rule.get("conditions", [])

        for condition in conditions:
            param = condition["parameter"]
            operator = condition["operator"]
            value = condition["value"]

            current_value = getattr(vital_signs, param, None)
            if current_value is None:
                return False

            if operator == "gt" and current_value <= value:
                return False
            elif operator == "lt" and current_value >= value:
                return False
            elif operator == "eq" and current_value != value:
                return False

        return True

    def get_ews_recommendations(self, score: float) -> List[str]:
        """Get recommendations based on EWS score"""
        if score >= 7:
            return [
                "Immediate medical review required",
                "Consider ICU transfer",
                "Continuous vital sign monitoring",
                "Prepare for rapid response team activation",
            ]
        elif score >= 5:
            return [
                "Urgent medical review within 30 minutes",
                "Increase monitoring frequency to every 15 minutes",
                "Notify charge nurse",
                "Prepare for potential deterioration",
            ]
        elif score >= 3:
            return [
                "Medical review within 1 hour",
                "Increase monitoring frequency to every 30 minutes",
                "Document assessment findings",
            ]
        else:
            return ["Continue routine monitoring"]

    def get_vital_sign_recommendations(
        self, param: str, value: float, severity: str
    ) -> List[str]:
        """Get recommendations for abnormal vital signs"""
        recommendations = []

        if param == "heart_rate":
            if value > 120:
                recommendations.extend(
                    [
                        "Check for pain, anxiety, or fever",
                        "Assess for cardiac symptoms",
                        "Consider ECG monitoring",
                        "Review medications",
                    ]
                )
            elif value < 50:
                recommendations.extend(
                    [
                        "Assess for symptoms of bradycardia",
                        "Check medication effects",
                        "Consider cardiac monitoring",
                    ]
                )

        elif param == "oxygen_saturation":
            if value < 90:
                recommendations.extend(
                    [
                        "Immediate oxygen therapy",
                        "Check airway and breathing",
                        "Consider ABG analysis",
                        "Prepare for intubation if severe",
                    ]
                )
            elif value < 95:
                recommendations.extend(
                    [
                        "Supplemental oxygen consideration",
                        "Reposition patient",
                        "Encourage deep breathing",
                    ]
                )

        elif param == "blood_pressure_systolic":
            if value > 180:
                recommendations.extend(
                    [
                        "Check for hypertensive urgency",
                        "Assess for headache, vision changes",
                        "Review antihypertensive medications",
                        "Consider immediate treatment",
                    ]
                )
            elif value < 90:
                recommendations.extend(
                    [
                        "Assess for shock symptoms",
                        "Check fluid status",
                        "Consider vasopressors if indicated",
                    ]
                )

        # Add general recommendations based on severity
        if severity in ["high", "critical"]:
            recommendations.append("Notify physician immediately")
            recommendations.append("Document interventions")

        return recommendations

    async def handle_alert(self, alert: PatientAlert):
        """Handle alert notification and escalation"""
        # Store alert in Redis
        await self.store_alert(alert)

        # Send WebSocket notification
        alert_message = {"type": "alert", "alert": alert.dict()}
        await self.connection_manager.broadcast(json.dumps(alert_message))

        # Send email notification for critical alerts
        if alert.severity == "critical":
            await self.send_email_alert(alert)

        # Log alert
        logger.warning(
            f"ALERT: {alert.alert_type} for patient {alert.patient_id} - {alert.severity}"
        )

    async def store_alert(self, alert: PatientAlert):
        """Store alert in Redis"""
        alert_key = f"alert:{alert.patient_id}:{alert.timestamp.isoformat()}"
        alert_data = alert.json()
        self.redis_client.setex(alert_key, 86400 * 7, alert_data)  # Store for 7 days

        # Add to patient alert list
        patient_alerts_key = f"patient_alerts:{alert.patient_id}"
        self.redis_client.lpush(patient_alerts_key, alert_data)
        self.redis_client.ltrim(patient_alerts_key, 0, 99)  # Keep last 100 alerts

    async def send_email_alert(self, alert: PatientAlert):
        """Send email alert for critical alerts"""
        if not self.email_config:
            return

        # Create email template
        template = Template(
            """
        Critical Patient Alert - HMS Monitoring System

        Patient ID: {{ patient_id }}
        Alert Type: {{ alert_type }}
        Severity: {{ severity }}
        Time: {{ timestamp }}
        Score: {{ score }}

        Message: {{ message }}

        Recommendations:
        {% for rec in recommendations %}
        - {{ rec }}
        {% endfor %}

        Please respond immediately.
        """
        )

        # Render email
        email_body = template.render(
            patient_id=alert.patient_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            timestamp=alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            score=alert.score,
            message=alert.message,
            recommendations=alert.recommendations,
        )

        # Send email
        try:
            msg = MIMEText(email_body)
            msg["Subject"] = f"CRITICAL ALERT: Patient {alert.patient_id}"
            msg["From"] = self.email_config["from_email"]
            msg["To"] = ", ".join(self.email_config["to_emails"])

            with smtplib.SMTP(
                self.email_config["smtp_server"], self.email_config["smtp_port"]
            ) as server:
                server.starttls()
                server.login(
                    self.email_config["username"], self.email_config["password"]
                )
                server.send_message(msg)

            logger.info(f"Email alert sent for patient {alert.patient_id}")
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    async def store_monitoring_state(
        self, patient_id: str, state: PatientMonitoringState
    ):
        """Store monitoring state in Redis"""
        # Convert to serializable format
        state_data = {
            "vital_signs_history": [vs.dict() for vs in state.vital_signs_history],
            "current_ews_score": state.current_ews_score,
            "last_update": state.last_update.isoformat(),
            "trend_data": state.trend_data,
        }

        self.redis_client.setex(
            f"monitoring_state:{patient_id}", 3600, json.dumps(state_data)  # 1 hour TTL
        )

    async def monitor_patients(self):
        """Background task to monitor all patients"""
        while True:
            try:
                for patient_id, state in self.monitored_patients.items():
                    # Check if patient needs update based on monitoring interval
                    interval = state.monitoring_config.monitoring_intervals.get(
                        "vital_signs", 300
                    )
                    if (
                        datetime.utcnow() - state.last_update
                    ).total_seconds() > interval:
                        # Request vital signs update
                        await self.request_vital_signs_update(patient_id)

                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)

    async def request_vital_signs_update(self, patient_id: str):
        """Request updated vital signs from monitoring devices"""
        # This would integrate with actual monitoring devices
        # For now, just log the request
        logger.debug(f"Requesting vital signs update for patient {patient_id}")

    async def check_system_health(self):
        """Check system health and performance"""
        while True:
            try:
                # Check Redis connection
                self.redis_client.ping()

                # Check number of monitored patients
                logger.info(
                    f"Currently monitoring {len(self.monitored_patients)} patients"
                )

                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"System health check failed: {e}")
                await asyncio.sleep(60)

    async def cleanup_old_data(self):
        """Clean up old monitoring data"""
        while True:
            try:
                # Clean up old vital signs history
                for patient_id, state in self.monitored_patients.items():
                    if len(state.vital_signs_history) > 1000:
                        state.vital_signs_history = state.vital_signs_history[-1000:]

                await asyncio.sleep(3600)  # Clean up every hour
            except Exception as e:
                logger.error(f"Data cleanup failed: {e}")
                await asyncio.sleep(3600)

    async def acknowledge_alert(
        self, patient_id: str, alert_timestamp: str, acknowledged_by: str
    ):
        """Acknowledge an alert"""
        # Find and update alert
        state = self.monitored_patients.get(patient_id)
        if state:
            for alert in state.alert_history:
                if (
                    alert.timestamp.isoformat() == alert_timestamp
                    and not alert.acknowledged
                ):
                    alert.acknowledged = True
                    alert.acknowledged_by = acknowledged_by
                    alert.acknowledged_time = datetime.utcnow()

                    # Update in Redis
                    await self.store_alert(alert)

                    # Broadcast update
                    update = {
                        "type": "alert_acknowledged",
                        "patient_id": patient_id,
                        "alert_timestamp": alert_timestamp,
                        "acknowledged_by": acknowledged_by,
                    }
                    await self.connection_manager.broadcast(json.dumps(update))

                    break

    async def resolve_alert(self, patient_id: str, alert_timestamp: str):
        """Mark an alert as resolved"""
        state = self.monitored_patients.get(patient_id)
        if state:
            for alert in state.alert_history:
                if alert.timestamp.isoformat() == alert_timestamp:
                    alert.resolved_time = datetime.utcnow()

                    # Update in Redis
                    await self.store_alert(alert)

                    # Broadcast update
                    update = {
                        "type": "alert_resolved",
                        "patient_id": patient_id,
                        "alert_timestamp": alert_timestamp,
                    }
                    await self.connection_manager.broadcast(json.dumps(update))

                    break

    def get_patient_status(self, patient_id: str) -> Optional[Dict]:
        """Get current patient monitoring status"""
        state = self.monitored_patients.get(patient_id)
        if not state:
            return None

        return {
            "patient_id": patient_id,
            "monitoring_level": state.monitoring_config.monitoring_level,
            "current_ews_score": state.current_ews_score,
            "last_update": state.last_update.isoformat(),
            "active_alerts": len(
                [a for a in state.alert_history if not a.resolved_time]
            ),
            "vital_signs": (
                state.vital_signs_history[-1].dict()
                if state.vital_signs_history
                else None
            ),
        }


# FastAPI app
app = FastAPI(title="HMS Real-time Patient Monitoring", version="1.0.0")

# Initialize monitoring system
monitoring_config = {
    "redis": {"host": "localhost", "port": 6379},
    "database": {"host": "localhost", "database": "hms"},
    "email": {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "from_email": "alerts@hospital.com",
        "to_emails": ["doctor@hospital.com", "nurse@hospital.com"],
        "username": "alerts@hospital.com",
        "password": "password",
    },
}

monitoring_system = RealtimePatientMonitoringSystem(monitoring_config)


@app.websocket("/ws/monitoring")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time monitoring updates"""
    await monitoring_system.connection_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages
            message = json.loads(data)
            if message["type"] == "acknowledge_alert":
                await monitoring_system.acknowledge_alert(
                    message["patient_id"],
                    message["alert_timestamp"],
                    message["acknowledged_by"],
                )
            elif message["type"] == "resolve_alert":
                await monitoring_system.resolve_alert(
                    message["patient_id"], message["alert_timestamp"]
                )
    except WebSocketDisconnect:
        monitoring_system.connection_manager.disconnect(websocket)


@app.post("/monitoring/add")
async def add_patient_to_monitoring(config: MonitoringConfig):
    """Add patient to monitoring system"""
    await monitoring_system.add_patient_to_monitoring(config)
    return {
        "status": "success",
        "message": f"Patient {config.patient_id} added to monitoring",
    }


@app.post("/monitoring/update-vitals")
async def update_vital_signs(patient_id: str, vital_signs: VitalSigns):
    """Update patient vital signs"""
    await monitoring_system.update_vital_signs(patient_id, vital_signs)
    return {"status": "success", "message": "Vital signs updated"}


@app.get("/monitoring/status/{patient_id}")
async def get_patient_status(patient_id: str):
    """Get patient monitoring status"""
    status = monitoring_system.get_patient_status(patient_id)
    if not status:
        raise HTTPException(
            status_code=404, detail="Patient not found in monitoring system"
        )
    return status


@app.get("/monitoring/alerts/{patient_id}")
async def get_patient_alerts(patient_id: str, limit: int = 10):
    """Get patient alert history"""
    alerts_key = f"patient_alerts:{patient_id}"
    alerts_data = monitoring_system.redis_client.lrange(alerts_key, 0, limit - 1)
    alerts = [json.loads(data) for data in alerts_data]
    return {"alerts": alerts}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/metrics")
async def get_metrics():
    """Get Prometheus metrics"""
    return prometheus_client.generate_latest()


# Example usage
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
