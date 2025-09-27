"""
main module
"""

import json
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from threading import Thread

import requests
from fastapi import Depends, FastAPI, Header, HTTPException
from jose import JWTError, jwt
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

try:
    from kafka import KafkaConsumer
except Exception:
    KafkaConsumer = None
DATABASE_URL = os.getenv(
    "NOTIFICATIONS_DATABASE_URL",
    os.getenv("DATABASE_URL", "sqlite:///./notifications.db"),
)
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
app = FastAPI(title="Notifications Service", version="1.2.0")
Instrumentator().instrument(app).expose(app)


class NotificationModel(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    channel = Column(String(20), nullable=False)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), default="queued", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)


def create_tables():
    Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def on_startup():
    create_tables()
    _load_secrets_from_vault()
    _start_kafka_consumer()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_auth(authorization: str | None = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


class SendPayload(BaseModel):
    channel: str
    recipient: str
    subject: str
    message: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/notifications/send")
def send(
    payload: SendPayload,
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    role = claims.get("role")
    if role not in {"SUPER_ADMIN", "HOSPITAL_ADMIN"}:
        raise HTTPException(status_code=403, detail="Forbidden")
    row = NotificationModel(
        channel=payload.channel,
        recipient=payload.recipient,
        subject=payload.subject,
        message=payload.message,
        status="queued",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    try:
        if payload.channel.lower() == "email":
            _send_email(payload.recipient, payload.subject, payload.message)
        elif payload.channel.lower() == "sms":
            _send_sms(payload.recipient, payload.message)
        elif payload.channel.lower() in {"push", "fcm"}:
            _send_fcm(
                payload.recipient,
                payload.title if hasattr(payload, "title") else payload.subject,
                payload.message,
            )
        else:
            raise ValueError("Unsupported channel")
        row.status = "sent"
        row.sent_at = datetime.utcnow()
    except Exception:
        row.status = "failed"
    finally:
        db.add(row)
        db.commit()
    return {"status": row.status, "id": row.id}


@app.get("/api/notifications/history")
def history(_: dict = Depends(require_auth), db: Session = Depends(get_db)):
    rows = (
        db.query(NotificationModel)
        .order_by(NotificationModel.id.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id": r.id,
            "channel": r.channel,
            "recipient": r.recipient,
            "subject": r.subject,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "sent_at": r.sent_at.isoformat() if r.sent_at else None,
        }
        for r in rows
    ]


def _send_email(recipient: str, subject: str, body: str) -> None:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_SENDER", user or "noreply@example.com")
    if not host:
        return
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(host, port, timeout=10) as server:
        server.starttls()
        if user and password:
            server.login(user, password)
        server.send_message(msg)


def _send_sms(recipient: str, message: str) -> None:
    url = os.getenv("SMS_PROVIDER_URL")
    token = os.getenv("SMS_PROVIDER_TOKEN")
    if not url:
        return
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    payload = {"to": recipient, "message": message}
    r = requests.post(url, json=payload, headers=headers, timeout=10)
    r.raise_for_status()


def _send_fcm(recipient_token: str, title: str, body: str) -> None:
    server_key = os.getenv("FCM_SERVER_KEY")
    if not server_key:
        return
    headers = {"Authorization": f"key={server_key}", "Content-Type": "application/json"}
    payload = {"to": recipient_token, "notification": {"title": title, "body": body}}
    r = requests.post(
        "https://fcm.googleapis.com/fcm/send", json=payload, headers=headers, timeout=10
    )
    r.raise_for_status()


def _load_secrets_from_vault() -> None:
    addr = os.getenv("VAULT_ADDR")
    token = os.getenv("VAULT_TOKEN")
    path = os.getenv("VAULT_SECRET_PATH", "secret/data/notifications")
    if not (addr and token and path):
        return
    url = f"{addr.rstrip('/')}/v1/{path.lstrip('/')}"
    try:
        resp = requests.get(url, headers={"X-Vault-Token": token}, timeout=5)
        if not resp.ok:
            return
        data = resp.json().get("data", {}).get("data", {})
        for key in [
            "SMTP_HOST",
            "SMTP_PORT",
            "SMTP_USER",
            "SMTP_PASSWORD",
            "SMTP_SENDER",
            "SMS_PROVIDER_URL",
            "SMS_PROVIDER_TOKEN",
            "FCM_SERVER_KEY",
        ]:
            if key not in os.environ and key in data:
                os.environ[key] = str(data[key])
    except Exception:
        return


def _start_kafka_consumer():
    if KafkaConsumer is None:
        return
    broker = os.getenv("KAFKA_BROKER", "kafka:9092")
    topic = os.getenv("KAFKA_TOPIC_APPOINTMENTS", "appointments_events")

    def _run():
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=broker,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            )
            for msg in consumer:
                evt = msg.value
                if evt.get("event") == "appointment_created":
                    with SessionLocal() as db:
                        row = NotificationModel(
                            channel="email",
                            recipient="ops@example.com",
                            subject="New Appointment",
                            message=json.dumps(evt),
                            status="queued",
                        )
                        db.add(row)
                        db.commit()
        except Exception:
            return

    t = Thread(target=_run, daemon=True)
    t.start()
