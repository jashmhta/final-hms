"""Enhanced Mock TPA Service with Security and Realistic Processing"""

import json
import logging
import os
import random
import time
import uuid
from datetime import datetime
from threading import Lock

from cryptography.fernet import Fernet
from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread-safe mock database
mock_db_lock = Lock()
mock_db = {
    "preauths": {},
    "claims": {},
    "transactions": [],
    "config": {
        "approval_threshold": 5000,
        "reimbursement_rate": 0.9,
        "max_procedures": 5,
        "approval_rate": 0.85,  # 85% approval rate
    },
}

# Initialize Fernet for encryption
try:
    # In production, this would come from Django settings
    ENCRYPTION_KEY = os.environ.get(
        "MOCK_TPA_ENCRYPTION_KEY", Fernet.generate_key().decode()
    )
    fernet = Fernet(ENCRYPTION_KEY.encode())
    logger.info("Fernet encryption initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Fernet: {e}")
    fernet = Fernet(Fernet.generate_key())


# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "processed_transactions": len(mock_db["transactions"]),
            "config": mock_db["config"],
            "encryption_enabled": True,
        }
    )


@app.route("/api/tpa/pre-auth/", methods=["POST"])
def mock_pre_auth():
    """Mock TPA Pre-Authorization Endpoint with Realistic Processing"""
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")

        # Validate required fields
        required_fields = [
            "patient_id",
            "policy_number",
            "procedure_code",
            "estimated_amount",
        ]
        missing_fields = [
            field for field in required_fields if field not in data or not data[field]
        ]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {missing_fields}"}), 400

        # Encrypt sensitive data
        encrypted_patient_id = fernet.encrypt(data["patient_id"].encode()).decode()
        tpa_transaction_id = str(uuid.uuid4())
        policy_number = data["policy_number"]
        procedure_code = data["procedure_code"]
        estimated_amount = float(data.get("estimated_amount", 0))
        diagnosis_code = data.get("diagnosis_code", "")

        # Validate amount
        if estimated_amount <= 0:
            return jsonify({"error": "Estimated amount must be positive"}), 400
        if estimated_amount > 1000000:
            return (
                jsonify(
                    {"error": "Estimated amount exceeds maximum limit of $1,000,000"}
                ),
                400,
            )

        # Simulate realistic processing delay (2-5 seconds)
        processing_delay = random.uniform(2, 5)
        time.sleep(processing_delay)

        # Mock approval logic based on amount and policy rules
        approval_threshold = mock_db["config"]["approval_threshold"]
        approval_rate = mock_db["config"]["approval_rate"]

        status = "approved"
        approval_reason = "Pre-authorization approved within policy limits"

        if estimated_amount > approval_threshold:
            status = "rejected"
            approval_reason = f"Estimated amount ${estimated_amount:.2f} exceeds policy limit of ${approval_threshold}"
        elif random.random() > approval_rate:  # Rejection based on approval rate
            status = "rejected"
            approval_reason = "Insufficient policy coverage for specified procedure or random business rule"
        elif random.random() < 0.1:  # 10% random rejection for edge cases
            status = "rejected"
            approval_reason = (
                "Additional documentation required - please contact TPA support"
            )

        # Store in mock database (thread-safe)
        with mock_db_lock:
            preauth_record = {
                "id": tpa_transaction_id,
                "patient_id_encrypted": encrypted_patient_id,
                "policy_number": policy_number,
                "procedure_code": procedure_code,
                "estimated_amount": estimated_amount,
                "diagnosis_code": diagnosis_code,
                "status": status,
                "approval_reason": approval_reason,
                "processed_at": datetime.now().isoformat(),
                "processing_delay": round(processing_delay, 2),
                "request_data": {k: v for k, v in data.items() if k != "patient_id"},
            }
            mock_db["preauths"][tpa_transaction_id] = preauth_record
            mock_db["transactions"].append(
                {
                    "type": "preauth",
                    "id": tpa_transaction_id,
                    "status": status,
                    "amount": estimated_amount,
                    "timestamp": datetime.now().isoformat(),
                    "policy_number": policy_number,
                    "approval_reason": approval_reason,
                }
            )

        logger.info(
            f"Pre-auth processed: {tpa_transaction_id}, status: {status}, amount: ${estimated_amount:.2f}, delay: {processing_delay:.2f}s"
        )

        response = {
            "tpa_transaction_id": tpa_transaction_id,
            "status": status,
            "approval_reason": approval_reason,
            "processing_time_seconds": round(processing_delay, 2),
            "timestamp": datetime.now().isoformat(),
            "estimated_amount": estimated_amount,
            "policy_number": policy_number,
            "next_steps": {
                "approved": "Proceed with scheduled procedure. TPA approval confirmed.",
                "rejected": "Review policy coverage and contact TPA support for appeal process.",
            }.get(status, "Contact TPA support for further assistance"),
        }

        return jsonify(response), 200

    except BadRequest as e:
        logger.error(f"Bad request in pre-auth: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except ValueError as e:
        logger.error(f"Validation error in pre-auth: {str(e)}")
        return jsonify({"error": "Invalid data format", "details": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error in pre-auth: {str(e)}")
        return (
            jsonify(
                {"error": "Internal server error", "message": "Please try again later"}
            ),
            500,
        )


@app.route("/api/tpa/claim/", methods=["POST"])
def mock_claim_processing():
    """Mock TPA Claim Processing Endpoint with Reimbursement Simulation"""
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")

        # Validate required fields
        required_fields = [
            "patient_id",
            "policy_number",
            "claim_amount",
            "procedure_codes",
        ]
        missing_fields = [
            field for field in required_fields if field not in data or not data[field]
        ]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {missing_fields}"}), 400

        # Validate procedure codes
        procedure_codes = data.get("procedure_codes", [])
        if not isinstance(procedure_codes, list) or len(procedure_codes) == 0:
            return jsonify({"error": "procedure_codes must be a non-empty list"}), 400
        if len(procedure_codes) > 10:
            return (
                jsonify({"error": "Maximum 10 procedure codes allowed per claim"}),
                400,
            )

        # Validate claim amount
        claim_amount = float(data.get("claim_amount", 0))
        if claim_amount <= 0:
            return jsonify({"error": "Claim amount must be positive"}), 400
        if claim_amount > 500000:
            return (
                jsonify({"error": "Claim amount exceeds maximum limit of $500,000"}),
                400,
            )

        # Encrypt sensitive data
        encrypted_patient_id = fernet.encrypt(data["patient_id"].encode()).decode()
        tpa_transaction_id = str(uuid.uuid4())
        policy_number = data["policy_number"]
        diagnosis_codes = data.get("diagnosis_codes", [])
        procedure_count = len(procedure_codes)

        # Simulate longer processing delay (5-15 seconds)
        processing_delay = random.uniform(5, 15)
        time.sleep(processing_delay)

        # Mock claim processing logic with realistic business rules
        max_amount = 10000
        max_procedures = mock_db["config"]["max_procedures"]
        reimbursement_rate = mock_db["config"]["reimbursement_rate"]
        approval_rate = mock_db["config"]["approval_rate"]

        status = "approved"
        rejection_reason = None
        reimbursed_amount = 0
        approval_reason = None

        if claim_amount <= max_amount and procedure_count <= max_procedures:
            # Full approval for reasonable claims
            reimbursed_amount = min(claim_amount * reimbursement_rate, claim_amount)
            approval_reason = (
                f"Claim approved for full reimbursement of ${reimbursed_amount:.2f}"
            )
        elif claim_amount <= max_amount * 1.5 and procedure_count <= max_procedures * 2:
            # Partial approval for larger claims
            status = "partially_approved"
            reimbursed_amount = claim_amount * (reimbursement_rate * 0.7)
            approval_reason = f"Partial approval: ${reimbursed_amount:.2f} of ${claim_amount:.2f} due to high claim amount/multiple procedures"
        else:
            # Full rejection
            status = "rejected"
            rejection_reason = f"Claim rejected: Amount ${claim_amount:.2f} exceeds policy limits or {procedure_count} procedures exceed maximum of {max_procedures}"
            reimbursed_amount = 0

        # Random element for realism (5% rejection rate for edge cases)
        if random.random() < 0.05 and status != "rejected":
            status = "rejected"
            rejection_reason = "Additional review required - please contact TPA support for appeal process"
            reimbursed_amount = 0
            approval_reason = None

        # Store in mock database (thread-safe)
        with mock_db_lock:
            claim_record = {
                "id": tpa_transaction_id,
                "patient_id_encrypted": encrypted_patient_id,
                "policy_number": policy_number,
                "claim_amount": claim_amount,
                "reimbursed_amount": reimbursed_amount,
                "procedure_codes": procedure_codes,
                "diagnosis_codes": diagnosis_codes,
                "status": status,
                "rejection_reason": rejection_reason,
                "approval_reason": approval_reason,
                "processed_at": datetime.now().isoformat(),
                "processing_delay": round(processing_delay, 2),
                "request_data": {k: v for k, v in data.items() if k != "patient_id"},
            }
            mock_db["claims"][tpa_transaction_id] = claim_record
            mock_db["transactions"].append(
                {
                    "type": "claim",
                    "id": tpa_transaction_id,
                    "status": status,
                    "claim_amount": claim_amount,
                    "reimbursed_amount": reimbursed_amount,
                    "timestamp": datetime.now().isoformat(),
                    "policy_number": policy_number,
                    "procedure_count": procedure_count,
                    "rejection_reason": rejection_reason,
                }
            )

        logger.info(
            f"Claim processed: {tpa_transaction_id}, status: {status}, claim: ${claim_amount:.2f}, reimbursed: ${reimbursed_amount:.2f}, delay: {processing_delay:.2f}s"
        )

        response = {
            "tpa_transaction_id": tpa_transaction_id,
            "status": status,
            "claim_amount": claim_amount,
            "reimbursed_amount": reimbursed_amount,
            "rejection_reason": rejection_reason,
            "approval_reason": approval_reason,
            "processing_time_seconds": round(processing_delay, 2),
            "timestamp": datetime.now().isoformat(),
            "policy_number": policy_number,
            "procedure_count": procedure_count,
            "next_steps": {
                "approved": f"Reimbursement of ${reimbursed_amount:.2f} will be processed within 7-10 business days. Check your bank account or contact TPA for payment details.",
                "partially_approved": f"Partial reimbursement of ${reimbursed_amount:.2f} will be processed within 7-10 business days. Review claim details for remaining balance.",
                "rejected": "Please review rejection reason and contact TPA support to appeal the decision or submit additional documentation.",
            }.get(status, "Contact TPA support for further assistance"),
        }

        return jsonify(response), 200

    except BadRequest as e:
        logger.error(f"Bad request in claim processing: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except ValueError as e:
        logger.error(f"Validation error in claim processing: {str(e)}")
        return jsonify({"error": "Invalid data format", "details": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error in claim processing: {str(e)}")
        return (
            jsonify(
                {"error": "Internal server error", "message": "Please try again later"}
            ),
            500,
        )


@app.route("/api/tpa/status/<transaction_id>", methods=["GET"])
def get_transaction_status(transaction_id):
    """Get transaction status by ID with decryption support"""
    try:
        with mock_db_lock:
            # Check pre-auth first
            if transaction_id in mock_db["preauths"]:
                record = mock_db["preauths"][transaction_id].copy()
                # Decrypt patient_id for response
                try:
                    decrypted_patient_id = fernet.decrypt(
                        record["patient_id_encrypted"].encode()
                    ).decode()
                    record["patient_id"] = decrypted_patient_id
                except Exception as e:
                    logger.error(f"Decryption failed for preauth {transaction_id}: {e}")
                    record["patient_id"] = "***DECRYPTION_FAILED***"
                del record["patient_id_encrypted"]
                return jsonify(
                    {
                        "transaction_id": transaction_id,
                        "type": "preauth",
                        "status": record["status"],
                        "processed_at": record["processed_at"],
                        "data": record,
                        "message": "Pre-authorization status retrieved successfully",
                    }
                )

            # Check claims
            if transaction_id in mock_db["claims"]:
                record = mock_db["claims"][transaction_id].copy()
                # Decrypt patient_id for response
                try:
                    decrypted_patient_id = fernet.decrypt(
                        record["patient_id_encrypted"].encode()
                    ).decode()
                    record["patient_id"] = decrypted_patient_id
                except Exception as e:
                    logger.error(f"Decryption failed for claim {transaction_id}: {e}")
                    record["patient_id"] = "***DECRYPTION_FAILED***"
                del record["patient_id_encrypted"]
                return jsonify(
                    {
                        "transaction_id": transaction_id,
                        "type": "claim",
                        "status": record["status"],
                        "reimbursed_amount": record["reimbursed_amount"],
                        "processed_at": record["processed_at"],
                        "data": record,
                        "message": "Claim status retrieved successfully",
                    }
                )

        return (
            jsonify(
                {
                    "error": "Transaction not found",
                    "transaction_id": transaction_id,
                    "message": "No transaction found with the provided ID. Please verify the transaction ID and try again.",
                }
            ),
            404,
        )

    except Exception as e:
        logger.error(f"Error retrieving transaction status {transaction_id}: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "Failed to retrieve transaction status",
                }
            ),
            500,
        )


@app.route("/api/tpa/transactions", methods=["GET"])
def list_transactions():
    """List recent transactions (last 50)"""
    try:
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))

        with mock_db_lock:
            total_count = len(mock_db["transactions"])
            recent_transactions = mock_db["transactions"][offset : offset + limit]

        # Basic sanitization - don't include encrypted data
        sanitized_transactions = []
        for txn in recent_transactions:
            sanitized = txn.copy()
            if "patient_id_encrypted" in sanitized:
                del sanitized["patient_id_encrypted"]
            sanitized_transactions.append(sanitized)

        return jsonify(
            {
                "transactions": sanitized_transactions,
                "total_count": total_count,
                "current_offset": offset,
                "limit": limit,
                "has_more": offset + limit < total_count,
                "message": f"Retrieved {len(sanitized_transactions)} recent transactions",
            }
        )
    except Exception as e:
        logger.error(f"Error listing transactions: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "Failed to retrieve transaction list",
                }
            ),
            500,
        )


@app.route("/api/tpa/config", methods=["GET"])
def get_config():
    """Get mock TPA configuration"""
    try:
        config = mock_db["config"].copy()
        config["encryption_key_present"] = bool(
            os.environ.get("MOCK_TPA_ENCRYPTION_KEY")
        )
        config["server_time"] = datetime.now().isoformat()
        return jsonify(config)
    except Exception as e:
        logger.error(f"Error getting config: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "Failed to retrieve configuration",
                }
            ),
            500,
        )


# Utility functions for integration testing
def generate_mock_pre_auth_response(amount=None):
    """Generate mock pre-auth response for testing"""
    if amount is None:
        amount = random.uniform(100, 10000)
    status = "approved" if amount <= 5000 else random.choice(["approved", "rejected"])
    return {
        "tpa_transaction_id": str(uuid.uuid4()),
        "status": status,
        "approval_reason": (
            "Mock approval" if status == "approved" else "Mock rejection"
        ),
        "processing_time_seconds": random.uniform(2, 5),
        "estimated_amount": amount,
    }


def generate_mock_claim_response(amount=None, procedure_count=1):
    """Generate mock claim response for testing"""
    if amount is None:
        amount = random.uniform(500, 15000)
    if procedure_count is None:
        procedure_count = random.randint(1, 5)

    status = "approved" if amount <= 10000 else "partially_approved"
    reimbursed = amount * random.uniform(0.7, 0.95)

    return {
        "tpa_transaction_id": str(uuid.uuid4()),
        "status": status,
        "reimbursed_amount": reimbursed,
        "claim_amount": amount,
        "procedure_count": procedure_count,
        "processing_time_seconds": random.uniform(5, 15),
    }


if __name__ == "__main__":
    # Set Flask app configuration
    app.config["DEBUG"] = False
    app.config["JSON_SORT_KEYS"] = True
    app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

    # Start the mock TPA service
    port = int(os.environ.get("MOCK_TPA_PORT", 5000))
    logger.info(f"Starting Mock TPA Service on port {port}")
    logger.info("Mock TPA Service endpoints:")
    logger.info("- POST /api/tpa/pre-auth/")
    logger.info("- POST /api/tpa/claim/")
    logger.info("- GET /api/tpa/status/<transaction_id>")
    logger.info("- GET /api/tpa/transactions")
    logger.info("- GET /api/tpa/config")
    logger.info("- GET /health")

    app.run(host="0.0.0.0", port=port, threaded=True)
