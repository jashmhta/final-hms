"""
main module
"""

import os
from typing import List

from fastapi import Depends, FastAPI, Header, HTTPException
from jose import JWTError, jwt
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
app = FastAPI(title="Price Estimator Service", version="1.1.0")
Instrumentator().instrument(app).expose(app)


def require_auth(authorization: str | None = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


class EstimateItem(BaseModel):
    description: str
    quantity: int = 1
    unit_price_cents: int
    gst_rate: float = 0.18


class EstimateRequest(BaseModel):
    items: List[EstimateItem]
    discount_cents: int = 0


class EstimateResponse(BaseModel):
    subtotal_cents: int
    gst_cents: int
    discount_cents: int
    total_cents: int


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/estimator/estimate", response_model=EstimateResponse)
def estimate(payload: EstimateRequest, _: dict = Depends(require_auth)):
    subtotal = sum(i.quantity * i.unit_price_cents for i in payload.items)
    gst = 0
    for i in payload.items:
        gst += int(round(i.quantity * i.unit_price_cents * i.gst_rate))
    total = max(subtotal + gst - payload.discount_cents, 0)
    return EstimateResponse(
        subtotal_cents=subtotal,
        gst_cents=gst,
        discount_cents=payload.discount_cents,
        total_cents=total,
    )
