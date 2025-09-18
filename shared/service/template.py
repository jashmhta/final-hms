"""
Shared Service Template
Eliminates redundant service initialization and configuration.
"""

from typing import Optional, Dict, Any, Type
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import uvicorn
import logging
from datetime import datetime

from ..api.base import BaseServiceApp, create_success_response, create_error_response
from ..config.base import get_config, BaseConfig
from ..database.base import Base, HMSBaseModel
from ..database.crud import BaseCRUD


class BaseServiceTemplate:
    """Template for standardized microservices - eliminates redundant service setup."""

    def __init__(
        self,
        service_name: str,
        service_description: str,
        version: str = "1.0.0",
        port: int = 8000,
        database_model: Optional[Type[HMSBaseModel]] = None,
        crud_class: Optional[Type[BaseCRUD]] = None
    ):
        self.service_name = service_name
        self.service_description = service_description
        self.version = version
        self.port = port
        self.database_model = database_model
        self.crud_class = crud_class

        # Load configuration
        self.config = create_service_config(service_name, service_description, version, port)

        # Create service app
        self.service_app = BaseServiceApp(
            service_name=service_name,
            service_description=service_description,
            version=version
        )

        # Setup database
        self._setup_database()

        # Setup logging
        self._setup_logging()

        # Add error handlers
        self.service_app.add_error_handlers()

        # Add custom routes
        self._add_custom_routes()

    def _setup_database(self):
        """Setup database connection and session."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        self.engine = create_engine(
            self.config.get_database_url(),
            echo=self.config.debug
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        # Create tables
        if self.database_model:
            Base.metadata.create_all(bind=self.engine)

    def _setup_logging(self):
        """Setup standardized logging."""
        logging.basicConfig(
            level=getattr(logging, self.config.monitoring.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if self.config.monitoring.log_format == 'text' else None
        )
        self.logger = logging.getLogger(self.service_name)

    def _add_custom_routes(self):
        """Add custom routes to the service."""
        app = self.service_app.get_app()

        # Add CRUD routes if model and CRUD class provided
        if self.database_model and self.crud_class:
            self._add_crud_routes(app)

    def _add_crud_routes(self, app: FastAPI):
        """Add standard CRUD routes."""
        from ..database.crud import CreateSchemaType, UpdateSchemaType

        # Dependency to get database session
        def get_db():
            db = self.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        # CRUD routes
        @app.get(f"/{self.database_model.__tablename__.lower()}", response_model=list)
        async def list_items(
            skip: int = 0,
            limit: int = 100,
            db: Session = Depends(get_db)
        ):
            """List items with pagination."""
            crud = self.crud_class(self.database_model)
            items = crud.get_multi(db, skip=skip, limit=limit)
            return create_success_response(items)

        @app.get(f"/{self.database_model.__tablename__.lower()}/{{item_id}}")
        async def get_item(item_id: int, db: Session = Depends(get_db)):
            """Get single item by ID."""
            crud = self.crud_class(self.database_model)
            item = crud.get(db, item_id)
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            return create_success_response(item)

        @app.post(f"/{self.database_model.__tablename__.lower()}", status_code=201)
        async def create_item(item_data: CreateSchemaType, db: Session = Depends(get_db)):
            """Create new item."""
            crud = self.crud_class(self.database_model)
            item = crud.create(db, item_data)
            return create_success_response(item, message="Item created successfully")

        @app.put(f"/{self.database_model.__tablename__.lower()}/{{item_id}}")
        async def update_item(item_id: int, item_data: UpdateSchemaType, db: Session = Depends(get_db)):
            """Update existing item."""
            crud = self.crud_class(self.database_model)
            db_item = crud.get(db, item_id)
            if not db_item:
                raise HTTPException(status_code=404, detail="Item not found")
            item = crud.update(db, db_item, item_data)
            return create_success_response(item, message="Item updated successfully")

        @app.delete(f"/{self.database_model.__tablename__.lower()}/{{item_id}}")
        async def delete_item(item_id: int, db: Session = Depends(get_db)):
            """Delete item."""
            crud = self.crud_class(self.database_model)
            item = crud.delete(db, item_id)
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            return create_success_response(None, message="Item deleted successfully")

        # Analytics routes
        @app.get(f"/{self.database_model.__tablename__.lower()}/stats")
        async def get_stats(db: Session = Depends(get_db)):
            """Get basic statistics."""
            crud = self.crud_class(self.database_model)
            total_count = crud.count(db)
            return create_success_response({
                "total_count": total_count,
                "service": self.service_name,
                "timestamp": datetime.utcnow()
            })

    def add_custom_route(self, path: str, methods: list, endpoint_func, **kwargs):
        """Add custom route to the service."""
        app = self.service_app.get_app()
        app.add_api_route(path, endpoint_func, methods=methods, **kwargs)

    def add_middleware(self, middleware_class, **kwargs):
        """Add custom middleware."""
        app = self.service_app.get_app()
        app.add_middleware(middleware_class, **kwargs)

    def get_app(self) -> FastAPI:
        """Get the FastAPI application."""
        return self.service_app.get_app()

    def run(self, host: Optional[str] = None, port: Optional[int] = None):
        """Run the service."""
        host = host or self.config.service.host
        port = port or self.config.service.port

        self.logger.info(f"Starting {self.service_name} service on {host}:{port}")
        self.logger.info(f"Environment: {self.config.environment.value}")
        self.logger.info(f"Database URL: {self.config.get_database_url()}")

        uvicorn.run(
            self.get_app(),
            host=host,
            port=port,
            log_level=self.config.monitoring.log_level.lower()
        )


class ServiceBuilder:
    """Builder class for creating standardized services."""

    def __init__(self, service_name: str, service_description: str):
        self.service_name = service_name
        self.service_description = service_description
        self.version = "1.0.0"
        self.port = 8000
        self.database_model = None
        self.crud_class = None
        self.custom_routes = []
        self.middleware = []

    def set_version(self, version: str) -> 'ServiceBuilder':
        """Set service version."""
        self.version = version
        return self

    def set_port(self, port: int) -> 'ServiceBuilder':
        """Set service port."""
        self.port = port
        return self

    def set_database_model(self, model: Type[HMSBaseModel], crud_class: Type[BaseCRUD]) -> 'ServiceBuilder':
        """Set database model and CRUD class."""
        self.database_model = model
        self.crud_class = crud_class
        return self

    def add_custom_route(self, path: str, methods: list, endpoint_func, **kwargs) -> 'ServiceBuilder':
        """Add custom route."""
        self.custom_routes.append((path, methods, endpoint_func, kwargs))
        return self

    def add_middleware(self, middleware_class, **kwargs) -> 'ServiceBuilder':
        """Add middleware."""
        self.middleware.append((middleware_class, kwargs))
        return self

    def build(self) -> BaseServiceTemplate:
        """Build the service."""
        service = BaseServiceTemplate(
            service_name=self.service_name,
            service_description=self.service_description,
            version=self.version,
            port=self.port,
            database_model=self.database_model,
            crud_class=self.crud_class
        )

        # Add custom routes
        for path, methods, endpoint_func, kwargs in self.custom_routes:
            service.add_custom_route(path, methods, endpoint_func, **kwargs)

        # Add middleware
        for middleware_class, kwargs in self.middleware:
            service.add_middleware(middleware_class, **kwargs)

        return service


# Utility functions for service creation
def create_basic_service(
    service_name: str,
    service_description: str,
    version: str = "1.0.0",
    port: int = 8000
) -> BaseServiceTemplate:
    """Create a basic service without database."""
    return ServiceBuilder(service_name, service_description)\
        .set_version(version)\
        .set_port(port)\
        .build()


def create_crud_service(
    service_name: str,
    service_description: str,
    database_model: Type[HMSBaseModel],
    crud_class: Type[BaseCRUD],
    version: str = "1.0.0",
    port: int = 8000
) -> BaseServiceTemplate:
    """Create a service with CRUD operations."""
    return ServiceBuilder(service_name, service_description)\
        .set_version(version)\
        .set_port(port)\
        .set_database_model(database_model, crud_class)\
        .build()


def run_service(
    service_name: str,
    service_description: str,
    version: str = "1.0.0",
    port: int = 8000,
    **kwargs
):
    """Quick service creation and execution."""
    service = create_basic_service(service_name, service_description, version, port)
    service.run(**kwargs)