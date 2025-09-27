"""
HR Service - Refactored using Shared Libraries
Eliminates redundant service initialization code.
"""

from shared.service.template import create_basic_service


def create_hr_service():
    """Create HR service using shared template."""
    service = create_basic_service(
        service_name="HR Service",
        service_description="API for HR service in HMS Enterprise-Grade System",
        version="1.0.0",
        port=8000,
    )

    # Add custom routes
    app = service.get_app()

    @app.get("/")
    async def root():
        return {"message": "HR Service API", "status": "running"}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "hr"}

    return service


if __name__ == "__main__":
    service = create_hr_service()
    service.run()
