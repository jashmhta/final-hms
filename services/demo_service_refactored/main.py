"""
Refactored Demo Service using Shared Libraries
Demonstrates elimination of redundancy through shared components.
"""

from typing import Optional

from pydantic import BaseModel, Field
from shared.api.base import create_success_response
from shared.config.base import get_config
from shared.database.base import HMSBaseModel
from shared.database.crud import BaseCRUD, CreateSchemaType, UpdateSchemaType

# Import shared components - eliminates redundant code
from shared.service.template import ServiceBuilder, create_crud_service
from sqlalchemy import JSON, Boolean, Column, Integer, String, Text
from sqlalchemy.orm import Session


# Define service-specific models using shared base classes
class DemoModel(HMSBaseModel):
    """Demo model using shared base class - eliminates redundant model setup."""

    __tablename__ = "demo_records"

    # Additional fields specific to this service
    category = Column(String(100), nullable=False, index=True)
    priority = Column(Integer, default=1)
    tags = Column(JSON, nullable=True)
    custom_field = Column(String(500), nullable=True)


# Pydantic schemas using shared patterns
class DemoCreate(BaseModel):
    """Create schema using shared patterns."""

    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: str = Field(..., min_length=2, max_length=100)
    priority: int = Field(1, ge=1, le=10)
    tags: Optional[list] = Field(default_factory=list)
    custom_field: Optional[str] = Field(None, max_length=500)


class DemoUpdate(BaseModel):
    """Update schema using shared patterns."""

    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, min_length=2, max_length=100)
    priority: Optional[int] = Field(None, ge=1, le=10)
    tags: Optional[list] = Field(None)
    custom_field: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = Field(None)


class DemoResponse(BaseModel):
    """Response schema using shared patterns."""

    id: int
    name: str
    description: Optional[str]
    category: str
    priority: int
    tags: Optional[list]
    custom_field: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# CRUD operations using shared base class
class DemoCRUD(BaseCRUD[DemoModel, DemoCreate, DemoUpdate]):
    """CRUD operations using shared base class - eliminates redundant CRUD code."""

    pass


# Custom business logic using shared patterns
def get_demo_by_category(db: Session, category: str, skip: int = 0, limit: int = 100):
    """Custom business logic using shared database patterns."""
    return (
        db.query(DemoModel)
        .filter(DemoModel.category == category, DemoModel.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_high_priority_items(db: Session, priority_threshold: int = 5):
    """Another custom business logic function."""
    return (
        db.query(DemoModel)
        .filter(DemoModel.priority >= priority_threshold, DemoModel.is_active == True)
        .order_by(DemoModel.priority.desc())
        .all()
    )


# Analytics endpoint using shared patterns
def get_demo_analytics(db: Session):
    """Analytics using shared database patterns."""
    from sqlalchemy import func

    total_count = db.query(DemoModel).filter(DemoModel.is_active == True).count()
    category_counts = (
        db.query(DemoModel.category, func.count(DemoModel.id).label("count"))
        .filter(DemoModel.is_active == True)
        .group_by(DemoModel.category)
        .all()
    )

    priority_stats = (
        db.query(
            func.avg(DemoModel.priority).label("avg_priority"),
            func.min(DemoModel.priority).label("min_priority"),
            func.max(DemoModel.priority).label("max_priority"),
        )
        .filter(DemoModel.is_active == True)
        .first()
    )

    return {
        "total_items": total_count,
        "category_distribution": [
            {"category": cat, "count": count} for cat, count in category_counts
        ],
        "priority_statistics": {
            "average": (
                round(priority_stats.avg_priority, 2)
                if priority_stats.avg_priority
                else 0
            ),
            "minimum": priority_stats.min_priority,
            "maximum": priority_stats.max_priority,
        },
    }


# Create the service using shared builder pattern
def create_demo_service():
    """Create demo service using shared builder pattern."""
    service = (
        ServiceBuilder(
            service_name="Demo Service",
            service_description="Refactored demo service using shared libraries",
        )
        .set_version("1.0.0")
        .set_port(8001)
        .set_database_model(DemoModel, DemoCRUD)
        .build()
    )

    # Add custom routes using shared patterns
    app = service.get_app()

    @app.get("/demo/category/{category}")
    async def get_by_category(
        category: str,
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(service.get_db),
    ):
        """Custom route using shared patterns."""
        items = get_demo_by_category(db, category, skip, limit)
        return create_success_response(
            items, f"Found {len(items)} items in category '{category}'"
        )

    @app.get("/demo/high-priority")
    async def get_high_priority(
        threshold: int = 5, db: Session = Depends(service.get_db)
    ):
        """Custom route for high priority items."""
        items = get_high_priority_items(db, threshold)
        return create_success_response(items, f"Found {len(items)} high priority items")

    @app.get("/demo/analytics")
    async def get_analytics(db: Session = Depends(service.get_db)):
        """Analytics endpoint using shared patterns."""
        analytics = get_demo_analytics(db)
        return create_success_response(
            analytics, "Demo analytics retrieved successfully"
        )

    @app.post("/demo/batch")
    async def create_batch(
        items: list[DemoCreate], db: Session = Depends(service.get_db)
    ):
        """Batch creation using shared patterns."""
        crud = DemoCRUD(DemoModel)
        created_items = []
        for item_data in items:
            item = crud.create(db, item_data)
            created_items.append(item)

        return create_success_response(
            created_items, f"Successfully created {len(created_items)} items"
        )

    return service


# Configuration and startup
if __name__ == "__main__":
    print("Starting Refactored Demo Service...")
    print(
        "This service demonstrates the elimination of redundancy through shared libraries."
    )

    # Load configuration using shared patterns
    config = get_config()
    print(f"Environment: {config.environment.value}")
    print(f"Database URL: {config.get_database_url()}")

    # Create and run service
    service = create_demo_service()
    service.run()
