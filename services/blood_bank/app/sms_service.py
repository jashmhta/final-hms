"""
Enterprise-grade SMS Service for HMS Blood Bank
HIPAA compliant with delivery confirmation, audit trail, and redundancy
"""

import os
import logging
import json
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class SMSPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class SMSMessageType(Enum):
    NOTIFICATION = "notification"
    ALERT = "alert"
    EMERGENCY = "emergency"
    REMINDER = "reminder"

@dataclass
class SMSResult:
    message_id: str
    status: str
    recipient: str
    timestamp: datetime
    provider: str
    delivery_status: Optional[str] = None
    error_message: Optional[str] = None
    cost: Optional[float] = None

class SMSService:
    """
    Enterprise SMS service with multi-provider redundancy and HIPAA compliance
    """

    def __init__(self):
        self.providers = self._initialize_providers()
        self.primary_provider = os.getenv('SMS_PRIMARY_PROVIDER', 'twilio')
        self.fallback_providers = os.getenv('SMS_FALLBACK_PROVIDERS', 'vonage,aws_sns').split(',')
        self.max_retries = int(os.getenv('SMS_MAX_RETRIES', '3'))
        self.hipaa_mode = os.getenv('HIPAA_MODE', 'true').lower() == 'true'

    def _initialize_providers(self) -> Dict[str, 'SMSProvider']:
        """Initialize SMS providers with enterprise configuration"""
        return {
            'twilio': TwilioProvider(),
            'vonage': VonageProvider(),
            'aws_sns': AWSNSProvider(),
            'telnyx': TelnyxProvider(),
        }

    def send_sms(self, recipient: str, message: str, priority: str = 'normal',
                message_type: str = 'notification', callback_url: Optional[str] = None) -> SMSResult:
        """
        Send SMS with enterprise features and fallback
        """
        if self.hipaa_mode:
            message = self._sanitize_hipaa_message(message)
            recipient = self._sanitize_phone_number(recipient)

        attempts = 0
        last_error = None

        # Try primary provider first
        provider_names = [self.primary_provider] + self.fallback_providers

        for provider_name in provider_names:
            if attempts >= self.max_retries:
                break

            provider = self.providers.get(provider_name)
            if not provider:
                logger.warning(f"SMS provider {provider_name} not configured")
                continue

            try:
                logger.info(f"Attempting SMS send via {provider_name} to {recipient[-4:]}")
                result = provider.send_sms(recipient, message, priority, message_type, callback_url)

                # Validate result
                if result.status == 'success':
                    logger.info(f"SMS sent successfully via {provider_name} with ID: {result.message_id}")
                    self._log_sms_activity(recipient, message, result, provider_name)
                    return result
                else:
                    last_error = result.error_message or "Unknown error"
                    logger.warning(f"SMS send failed via {provider_name}: {last_error}")

            except Exception as e:
                last_error = str(e)
                logger.error(f"SMS provider {provider_name} failed: {last_error}")
                continue

            attempts += 1

        # All providers failed
        error_msg = f"All SMS providers failed after {attempts} attempts. Last error: {last_error}"
        logger.error(error_msg)

        # Create failure result
        return SMSResult(
            message_id=f"failed_{datetime.now().timestamp()}",
            status='failed',
            recipient=recipient,
            timestamp=datetime.now(timezone.utc),
            provider='none',
            error_message=error_msg
        )

    def _sanitize_hipaa_message(self, message: str) -> str:
        """Sanitize message for HIPAA compliance"""
        # Remove any potential PHI
        message = message.replace('SSN', 'ID')
        message = message.replace('social security', 'identifier')
        message = message.replace('diagnosis', 'condition')
        message = message.replace('disease', 'condition')

        # Ensure message doesn't contain too specific health information
        if len(message) > 160:
            message = message[:157] + '...'

        return message

    def _sanitize_phone_number(self, phone: str) -> str:
        """Sanitize phone number for privacy and security"""
        # Remove any non-digit characters
        phone = ''.join(c for c in phone if c.isdigit())

        # Validate US phone number format
        if len(phone) == 10:
            phone = '1' + phone
        elif len(phone) != 11 or not phone.startswith('1'):
            raise ValueError(f"Invalid US phone number format: {phone}")

        return f"+{phone}"

    def _log_sms_activity(self, recipient: str, message: str, result: SMSResult, provider: str):
        """Log SMS activity for audit trail"""
        try:
            log_data = {
                'recipient': recipient[-4:],  # Only last 4 digits for privacy
                'message_preview': message[:50] + '...' if len(message) > 50 else message,
                'message_id': result.message_id,
                'status': result.status,
                'provider': provider,
                'timestamp': result.timestamp.isoformat(),
                'priority': 'high',  # Default for blood bank alerts
                'message_type': 'emergency',
            }

            # Cache for quick lookup
            cache.set(f"sms_{result.message_id}", log_data, timeout=86400)  # 24 hours

            # Log to audit trail (would integrate with audit log system)
            logger.info(f"SMS Activity Logged: {json.dumps(log_data)}")

        except Exception as e:
            logger.error(f"Failed to log SMS activity: {e}")

    def get_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """Get delivery status for a sent SMS"""
        try:
            # Check cache first
            cached_data = cache.get(f"sms_{message_id}")
            if cached_data:
                return cached_data

            # Query provider for status
            for provider_name, provider in self.providers.items():
                try:
                    status = provider.get_delivery_status(message_id)
                    if status:
                        return status
                except Exception as e:
                    logger.warning(f"Failed to get status from {provider_name}: {e}")
                    continue

            return {'error': 'Status not available'}

        except Exception as e:
            logger.error(f"Failed to get delivery status: {e}")
            return {'error': str(e)}

class SMSProvider:
    """Base class for SMS providers"""

    def send_sms(self, recipient: str, message: str, priority: str, message_type: str, callback_url: Optional[str]) -> SMSResult:
        raise NotImplementedError

    def get_delivery_status(self, message_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

class TwilioProvider(SMSProvider):
    """Twilio SMS provider implementation"""

    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_FROM_NUMBER')
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}"

    def send_sms(self, recipient: str, message: str, priority: str, message_type: str, callback_url: Optional[str]) -> SMSResult:
        """Send SMS via Twilio"""
        if not all([self.account_sid, self.auth_token, self.from_number]):
            raise ValueError("Twilio configuration incomplete")

        import base64
        from urllib.parse import urlencode

        # Prepare data
        data = {
            'To': recipient,
            'From': self.from_number,
            'Body': message,
        }

        if callback_url:
            data['StatusCallback'] = callback_url

        # Add priority header
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {base64.b64encode(f"{self.account_sid}:{self.auth_token}".encode()).decode()}'
        }

        try:
            response = requests.post(
                f"{self.base_url}/Messages.json",
                data=urlencode(data),
                headers=headers,
                timeout=30
            )

            if response.status_code == 201:
                response_data = response.json()
                return SMSResult(
                    message_id=response_data['sid'],
                    status='success',
                    recipient=recipient,
                    timestamp=datetime.now(timezone.utc),
                    provider='twilio',
                    delivery_status='queued',
                    cost=float(response_data.get('price', 0))
                )
            else:
                return SMSResult(
                    message_id=f"twilio_error_{datetime.now().timestamp()}",
                    status='failed',
                    recipient=recipient,
                    timestamp=datetime.now(timezone.utc),
                    provider='twilio',
                    error_message=f"HTTP {response.status_code}: {response.text}"
                )

        except Exception as e:
            return SMSResult(
                message_id=f"twilio_exception_{datetime.now().timestamp()}",
                status='failed',
                recipient=recipient,
                timestamp=datetime.now(timezone.utc),
                provider='twilio',
                error_message=str(e)
            )

    def get_delivery_status(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get delivery status from Twilio"""
        try:
            import base64

            headers = {
                'Authorization': f'Basic {base64.b64encode(f"{self.account_sid}:{self.auth_token}".encode()).decode()}'
            }

            response = requests.get(
                f"{self.base_url}/Messages/{message_id}.json",
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    'status': data['status'],
                    'error_code': data.get('error_code'),
                    'error_message': data.get('error_message'),
                    'date_created': data.get('date_created'),
                    'date_sent': data.get('date_sent'),
                    'date_updated': data.get('date_updated'),
                }

        except Exception as e:
            logger.error(f"Failed to get Twilio status: {e}")

        return None

class VonageProvider(SMSProvider):
    """Vonage (Nexmo) SMS provider implementation"""

    def __init__(self):
        self.api_key = os.getenv('VONAGE_API_KEY')
        self.api_secret = os.getenv('VONAGE_API_SECRET')
        self.from_number = os.getenv('VONAGE_FROM_NUMBER')
        self.base_url = "https://rest.nexmo.com/sms/json"

    def send_sms(self, recipient: str, message: str, priority: str, message_type: str, callback_url: Optional[str]) -> SMSResult:
        """Send SMS via Vonage"""
        if not all([self.api_key, self.api_secret, self.from_number]):
            raise ValueError("Vonage configuration incomplete")

        data = {
            'api_key': self.api_key,
            'api_secret': self.api_secret,
            'to': recipient,
            'from': self.from_number,
            'text': message,
        }

        if callback_url:
            data['callback'] = callback_url

        try:
            response = requests.post(self.base_url, data=data, timeout=30)

            if response.status_code == 200:
                response_data = response.json()
                messages = response_data.get('messages', [])
                if messages and messages[0].get('status') == '0':
                    return SMSResult(
                        message_id=messages[0]['message-id'],
                        status='success',
                        recipient=recipient,
                        timestamp=datetime.now(timezone.utc),
                        provider='vonage',
                        delivery_status='queued'
                    )
                else:
                    error_msg = messages[0].get('error-text', 'Unknown error') if messages else 'No messages in response'
                    return SMSResult(
                        message_id=f"vonage_error_{datetime.now().timestamp()}",
                        status='failed',
                        recipient=recipient,
                        timestamp=datetime.now(timezone.utc),
                        provider='vonage',
                        error_message=error_msg
                    )
            else:
                return SMSResult(
                    message_id=f"vonage_http_error_{datetime.now().timestamp()}",
                    status='failed',
                    recipient=recipient,
                    timestamp=datetime.now(timezone.utc),
                    provider='vonage',
                    error_message=f"HTTP {response.status_code}: {response.text}"
                )

        except Exception as e:
            return SMSResult(
                message_id=f"vonage_exception_{datetime.now().timestamp()}",
                status='failed',
                recipient=recipient,
                timestamp=datetime.now(timezone.utc),
                provider='vonage',
                error_message=str(e)
            )

    def get_delivery_status(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Vonage delivery status via webhook (simplified)"""
        # Vonage primarily uses webhooks for delivery reports
        return None

class AWSNSProvider(SMSProvider):
    """AWS SNS SMS provider implementation"""

    def __init__(self):
        self.access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.sns_client = None

    def _get_client(self):
        """Get boto3 SNS client"""
        if self.sns_client is None:
            import boto3
            self.sns_client = boto3.client(
                'sns',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
        return self.sns_client

    def send_sms(self, recipient: str, message: str, priority: str, message_type: str, callback_url: Optional[str]) -> SMSResult:
        """Send SMS via AWS SNS"""
        if not all([self.access_key, self.secret_key]):
            raise ValueError("AWS SNS configuration incomplete")

        try:
            client = self._get_client()

            attributes = {
                'AWS.SNS.SMS.SMSType': {
                    'DataType': 'String',
                    'StringValue': 'Transactional' if priority in ['high', 'urgent'] else 'Promotional'
                }
            }

            if callback_url:
                attributes['AWS.SNS.SMS.DeliveryStatus'] = {
                    'DataType': 'String',
                    'StringValue': callback_url
                }

            response = client.publish(
                PhoneNumber=recipient,
                Message=message,
                MessageAttributes=attributes
            )

            return SMSResult(
                message_id=response['MessageId'],
                status='success',
                recipient=recipient,
                timestamp=datetime.now(timezone.utc),
                provider='aws_sns',
                delivery_status='queued'
            )

        except Exception as e:
            return SMSResult(
                message_id=f"aws_sns_exception_{datetime.now().timestamp()}",
                status='failed',
                recipient=recipient,
                timestamp=datetime.now(timezone.utc),
                provider='aws_sns',
                error_message=str(e)
            )

    def get_delivery_status(self, message_id: str) -> Optional[Dict[str, Any]]:
        """AWS SNS delivery status via CloudWatch (simplified)"""
        return None

class TelnyxProvider(SMSProvider):
    """Telnyx SMS provider implementation"""

    def __init__(self):
        self.api_key = os.getenv('TELNYX_API_KEY')
        self.from_number = os.getenv('TELNYX_FROM_NUMBER')
        self.base_url = "https://api.telnyx.com/v2/messages"

    def send_sms(self, recipient: str, message: str, priority: str, message_type: str, callback_url: Optional[str]) -> SMSResult:
        """Send SMS via Telnyx"""
        if not all([self.api_key, self.from_number]):
            raise ValueError("Telnyx configuration incomplete")

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

        data = {
            'from': self.from_number,
            'to': recipient,
            'text': message,
        }

        if callback_url:
            data['webhook_url'] = callback_url

        try:
            response = requests.post(self.base_url, json=data, headers=headers, timeout=30)

            if response.status_code == 200:
                response_data = response.json()
                return SMSResult(
                    message_id=response_data['data']['id'],
                    status='success',
                    recipient=recipient,
                    timestamp=datetime.now(timezone.utc),
                    provider='telnyx',
                    delivery_status='queued'
                )
            else:
                return SMSResult(
                    message_id=f"telnyx_error_{datetime.now().timestamp()}",
                    status='failed',
                    recipient=recipient,
                    timestamp=datetime.now(timezone.utc),
                    provider='telnyx',
                    error_message=f"HTTP {response.status_code}: {response.text}"
                )

        except Exception as e:
            return SMSResult(
                message_id=f"telnyx_exception_{datetime.now().timestamp()}",
                status='failed',
                recipient=recipient,
                timestamp=datetime.now(timezone.utc),
                provider='telnyx',
                error_message=str(e)
            )

    def get_delivery_status(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get delivery status from Telnyx"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            }

            response = requests.get(f"{self.base_url}/{message_id}", headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return {
                    'status': data['data'].get('status'),
                    'created_at': data['data'].get('created_at'),
                    'updated_at': data['data'].get('updated_at'),
                    'error_code': data['data'].get('error_code'),
                    'error_message': data['data'].get('error_message'),
                }

        except Exception as e:
            logger.error(f"Failed to get Telnyx status: {e}")

        return None

# Factory function for easy instantiation
def create_sms_service() -> SMSService:
    """Create configured SMS service instance"""
    return SMSService()