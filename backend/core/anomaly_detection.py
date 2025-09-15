import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class MLAnomalyDetector:
    """ML-based anomaly detection for security monitoring"""

    def __init__(self):
        self.model_path = os.path.join(settings.BASE_DIR, 'ml_models')
        os.makedirs(self.model_path, exist_ok=True)
        self.scaler = StandardScaler()

    def train_user_behavior_model(self, user_id: int, behavior_data: List[Dict]) -> bool:
        """Train anomaly detection model for user behavior"""
        try:
            if len(behavior_data) < 10:
                logger.warning(f"Insufficient data for user {user_id}")
                return False

            # Extract features
            features = self._extract_behavior_features(behavior_data)

            # Train Isolation Forest
            model = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )

            # Fit and scale data
            scaled_features = self.scaler.fit_transform(features)
            model.fit(scaled_features)

            # Save model
            model_file = os.path.join(self.model_path, f'user_{user_id}_behavior.pkl')
            joblib.dump(model, model_file)

            logger.info(f"Trained behavior model for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to train model for user {user_id}: {e}")
            return False

    def detect_anomalies(self, user_id: int, current_behavior: Dict) -> Tuple[bool, float]:
        """Detect anomalies in user behavior"""
        try:
            model_file = os.path.join(self.model_path, f'user_{user_id}_behavior.pkl')

            if not os.path.exists(model_file):
                return False, 0.5  # No model available

            model = joblib.load(model_file)

            # Extract features from current behavior
            features = self._extract_single_behavior_features(current_behavior)
            scaled_features = self.scaler.transform([features])

            # Predict anomaly score
            scores = model.decision_function(scaled_features)
            anomaly_score = -scores[0]  # Convert to 0-1 scale

            # Predict if anomalous
            prediction = model.predict(scaled_features)
            is_anomaly = prediction[0] == -1

            return is_anomaly, float(anomaly_score)

        except Exception as e:
            logger.error(f"Failed to detect anomalies for user {user_id}: {e}")
            return False, 0.5

    def _extract_behavior_features(self, behavior_data: List[Dict]) -> np.ndarray:
        """Extract features from behavior data"""
        features = []

        for data in behavior_data:
            feature_vector = self._extract_single_behavior_features(data)
            features.append(feature_vector)

        return np.array(features)

    def _extract_single_behavior_features(self, behavior: Dict) -> List[float]:
        """Extract features from single behavior instance"""
        features = []

        # Time-based features
        hour = behavior.get('hour', 12)
        features.extend([
            hour / 24,  # Normalized hour
            1 if 9 <= hour <= 17 else 0,  # Business hours
            1 if hour in [0, 1, 2, 22, 23] else 0,  # Unusual hours
        ])

        # Location-based features
        location_consistent = behavior.get('location_consistent', 0.5)
        features.append(location_consistent)

        # Device features
        device_trust = behavior.get('device_trust_score', 50) / 100
        features.append(device_trust)

        # Session features
        session_duration = behavior.get('session_duration', 1800) / 3600  # Normalize to hours
        features.append(min(session_duration, 8))  # Cap at 8 hours

        # Activity patterns
        request_frequency = behavior.get('requests_per_minute', 10) / 60
        features.append(min(request_frequency, 10))  # Cap at 10 req/min

        # Authentication patterns
        failed_attempts = behavior.get('recent_failed_attempts', 0)
        features.append(min(failed_attempts, 5) / 5)  # Normalize

        return features


class BehavioralAnalytics:
    """Behavioral analytics for threat detection"""

    def __init__(self):
        self.cache_timeout = 3600  # 1 hour

    def analyze_user_behavior(self, user_id: int, current_session: Dict) -> Dict:
        """Analyze user behavior patterns"""
        # Get historical data
        historical_sessions = self._get_user_session_history(user_id)

        analysis = {
            'risk_score': 0,
            'anomalies': [],
            'recommendations': [],
            'confidence': 0.5
        }

        if len(historical_sessions) < 5:
            analysis['recommendations'].append('Insufficient historical data')
            return analysis

        # Analyze time patterns
        time_anomaly = self._analyze_time_patterns(current_session, historical_sessions)
        if time_anomaly:
            analysis['anomalies'].append(time_anomaly)
            analysis['risk_score'] += 20

        # Analyze location patterns
        location_anomaly = self._analyze_location_patterns(current_session, historical_sessions)
        if location_anomaly:
            analysis['anomalies'].append(location_anomaly)
            analysis['risk_score'] += 25

        # Analyze device patterns
        device_anomaly = self._analyze_device_patterns(current_session, historical_sessions)
        if device_anomaly:
            analysis['anomalies'].append(device_anomaly)
            analysis['risk_score'] += 15

        # Analyze activity patterns
        activity_anomaly = self._analyze_activity_patterns(current_session, historical_sessions)
        if activity_anomaly:
            analysis['anomalies'].append(activity_anomaly)
            analysis['risk_score'] += 20

        # Calculate confidence based on data quality
        analysis['confidence'] = min(0.9, len(historical_sessions) / 20)

        return analysis

    def _get_user_session_history(self, user_id: int) -> List[Dict]:
        """Get user's recent session history"""
        cache_key = f"user_sessions_{user_id}"
        sessions = cache.get(cache_key)

        if sessions is None:
            # In production, fetch from database
            sessions = []
            cache.set(cache_key, sessions, self.cache_timeout)

        return sessions

    def _analyze_time_patterns(self, current: Dict, historical: List[Dict]) -> Optional[str]:
        """Analyze login time patterns"""
        current_hour = current.get('hour', 12)
        historical_hours = [s.get('hour', 12) for s in historical]

        if not historical_hours:
            return None

        avg_hour = sum(historical_hours) / len(historical_hours)
        std_hour = np.std(historical_hours) if len(historical_hours) > 1 else 2

        if abs(current_hour - avg_hour) > 3 * std_hour:
            return f"Unusual login time: {current_hour}:00 (typical: {avg_hour:.1f}:00)"

        return None

    def _analyze_location_patterns(self, current: Dict, historical: List[Dict]) -> Optional[str]:
        """Analyze location patterns"""
        current_location = current.get('location')
        if not current_location:
            return None

        # Simple distance-based analysis
        known_locations = [s.get('location') for s in historical if s.get('location')]
        if not known_locations:
            return "First time from this location"

        # In production, use geolocation distance calculation
        if current_location not in known_locations:
            return "Unusual location detected"

        return None

    def _analyze_device_patterns(self, current: Dict, historical: List[Dict]) -> Optional[str]:
        """Analyze device usage patterns"""
        current_device = current.get('device_fingerprint')
        if not current_device:
            return None

        known_devices = [s.get('device_fingerprint') for s in historical if s.get('device_fingerprint')]
        if current_device not in known_devices:
            return "Unrecognized device"

        return None

    def _analyze_activity_patterns(self, current: Dict, historical: List[Dict]) -> Optional[str]:
        """Analyze user activity patterns"""
        current_requests = current.get('requests_count', 0)
        historical_requests = [s.get('requests_count', 0) for s in historical]

        if not historical_requests:
            return None

        avg_requests = sum(historical_requests) / len(historical_requests)
        if current_requests > 3 * avg_requests and current_requests > 100:
            return f"Unusually high activity: {current_requests} requests"

        return None


class RealTimeSecurityMonitor:
    """Real-time security monitoring system"""

    def __init__(self):
        self.alert_thresholds = {
            'failed_logins': 5,
            'suspicious_ips': 3,
            'unusual_activity': 10,
        }

    def monitor_request(self, request_data: Dict) -> List[Dict]:
        """Monitor incoming request for security threats"""
        alerts = []

        # Check for brute force attempts
        if self._check_brute_force(request_data):
            alerts.append({
                'type': 'BRUTE_FORCE',
                'severity': 'HIGH',
                'message': 'Potential brute force attack detected'
            })

        # Check for suspicious patterns
        if self._check_suspicious_patterns(request_data):
            alerts.append({
                'type': 'SUSPICIOUS_ACTIVITY',
                'severity': 'MEDIUM',
                'message': 'Suspicious activity pattern detected'
            })

        # Check for anomalous behavior
        anomaly_alert = self._check_behavioral_anomalies(request_data)
        if anomaly_alert:
            alerts.append(anomaly_alert)

        return alerts

    def _check_brute_force(self, request_data: Dict) -> bool:
        """Check for brute force attack patterns"""
        ip = request_data.get('ip_address')
        username = request_data.get('username')

        if not ip or not username:
            return False

        # Check failed login attempts from this IP
        cache_key = f"failed_logins_{ip}_{username}"
        failed_count = cache.get(cache_key, 0)

        return failed_count >= self.alert_thresholds['failed_logins']

    def _check_suspicious_patterns(self, request_data: Dict) -> bool:
        """Check for suspicious request patterns"""
        user_agent = request_data.get('user_agent', '').lower()
        suspicious_patterns = [
            'sqlmap', 'nmap', 'metasploit', 'burp', 'owasp',
            'acunetix', 'nessus', 'qualys', 'rapid7'
        ]

        return any(pattern in user_agent for pattern in suspicious_patterns)

    def _check_behavioral_anomalies(self, request_data: Dict) -> Optional[Dict]:
        """Check for behavioral anomalies"""
        user_id = request_data.get('user_id')
        if not user_id:
            return None

        detector = MLAnomalyDetector()
        is_anomaly, score = detector.detect_anomalies(user_id, request_data)

        if is_anomaly and score > 0.7:
            return {
                'type': 'BEHAVIORAL_ANOMALY',
                'severity': 'HIGH',
                'message': f'Behavioral anomaly detected (score: {score:.2f})'
            }

        return None


# Global instances
ml_detector = MLAnomalyDetector()
behavior_analytics = BehavioralAnalytics()
security_monitor = RealTimeSecurityMonitor()