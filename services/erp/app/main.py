from fastapi import FastAPI
from . import models
from .database import engine
from .routes import router as chart_router
models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="ERP Service")
app.include_router(chart_router)
@app.get("/health")
def health():
    return {"status": "ok"}