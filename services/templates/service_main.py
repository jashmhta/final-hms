from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
def create_service_app(service_name: str, service_description: str, version: str = "1.0.0") -> FastAPI:
    app = FastAPI(
        title=f"{service_name} Service API",
        description=f"{service_description} in HMS Enterprise-Grade System",
        version=version
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
        return {"message": f"{service_name} Service API", "status": "running"}
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": service_name.lower()}
    return app
def run_service(app: FastAPI, port: int = 8000):
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)