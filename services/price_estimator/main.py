"""
main module
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Price_Estimator Service API",
    description="API for price_estimator service in HMS Enterprise-Grade System",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Price_Estimator Service API", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "price_estimator"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
