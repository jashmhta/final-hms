from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(
    title="Ot_Scheduling Service API",
    description="API for ot_scheduling service in HMS Enterprise-Grade System",
    version="1.0.0"
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
    return {"message": "Ot_Scheduling Service API", "status": "running"}
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ot_scheduling"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)