"""
Radiology Service - Refactored using Shared Libraries
Eliminates redundant service initialization code.
"""

from shared.service.template import create_basic_service


def create_radiology_service():
    """Create radiology service using shared template."""
    service = create_basic_service(
        service_name="Radiology Service",
        service_description="API for radiology service in HMS Enterprise-Grade System",
        version="1.0.0",
        port=8000,
    )

    # Add custom routes
    app = service.get_app()

    @app.get("/")
    async def root():
        return {"message": "Radiology Service API", "status": "running"}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "radiology"}

    return service


if __name__ == "__main__":
    service = create_radiology_service()
    service.run()
