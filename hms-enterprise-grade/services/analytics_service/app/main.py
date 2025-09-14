import os
from datetime import datetime, timedelta

import requests
from fastapi import Depends, FastAPI, Header, HTTPException
from jose import JWTError, jwt
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import create_engine, text

app = FastAPI(title="Analytics Service", version="1.2.0")
Instrumentator().instrument(app).expose(app)

JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
DATABASE_URL = os.getenv(
    "ANALYTICS_DATABASE_URL", os.getenv("DATABASE_URL", "sqlite:///./analytics.db")
)
OPA_URL = os.getenv("OPA_URL")
engine = create_engine(DATABASE_URL)


def require_auth(authorization: str | None = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/analytics/overview")
def overview(_: dict = Depends(require_auth)):
    if OPA_URL:
        try:
            d = requests.post(
                f"{OPA_URL}/v1/data/hms/allow",
                json={"input": {"path": "/api/analytics/overview"}},
                timeout=2,
            )
            if d.ok and d.json().get("result") is False:
                raise HTTPException(status_code=403, detail="Policy denied")
        except Exception:
            pass
    with engine.connect() as conn:
        patients = (
            conn.execute(
                text("SELECT COUNT(*) FROM patients_patient")
            ).scalar_one_or_none()
            or 0
        )
        appt_today = (
            conn.execute(
                text(
                    "SELECT COUNT(*) FROM appointments_appointment WHERE DATE(start_at) = CURRENT_DATE"
                )
            ).scalar_one_or_none()
            or 0
        )
        revenue = (
            conn.execute(
                text("SELECT COALESCE(SUM(net_cents),0) FROM billing_bill")
            ).scalar_one_or_none()
            or 0
        )
    return {
        "patients_count": int(patients),
        "appointments_today": int(appt_today),
        "revenue_cents": int(revenue),
    }


@app.get("/api/analytics/appointments_trend")
def appointments_trend(days: int = 14, _: dict = Depends(require_auth)):
    if days <= 0 or days > 60:
        days = 14
    today = datetime.utcnow().date()
    start = today - timedelta(days=days - 1)
    out = []
    with engine.connect() as conn:
        d = start
        while d <= today:
            cnt = (
                conn.execute(
                    text(
                        "SELECT COUNT(*) FROM appointments_appointment WHERE DATE(start_at) = :d"
                    ),
                    {"d": d.isoformat()},
                ).scalar_one_or_none()
                or 0
            )
            out.append({"date": d.isoformat(), "appointments": int(cnt)})
            d = d + timedelta(days=1)
    return out


@app.get("/api/analytics/revenue_trend")
def revenue_trend(days: int = 14, _: dict = Depends(require_auth)):
    if days <= 0 or days > 60:
        days = 14
    today = datetime.utcnow().date()
    start = today - timedelta(days=days - 1)
    out = []
    with engine.connect() as conn:
        d = start
        while d <= today:
            rev = (
                conn.execute(
                    text(
                        "SELECT COALESCE(SUM(net_cents),0) FROM billing_bill WHERE DATE(updated_at) = :d"
                    ),
                    {"d": d.isoformat()},
                ).scalar_one_or_none()
                or 0
            )
            out.append({"date": d.isoformat(), "revenue_cents": int(rev)})
            d = d + timedelta(days=1)
    return out


@app.get("/api/analytics/department_revenue")
def department_revenue(_: dict = Depends(require_auth)):
    with engine.connect() as conn:
        rows = (
            conn.execute(
                text(
                    "SELECT department, COALESCE(SUM(amount_cents),0) AS total FROM billing_billlineitem GROUP BY department"
                )
            )
            .mappings()
            .all()
        )
        return {r["department"]: int(r["total"]) for r in rows}
