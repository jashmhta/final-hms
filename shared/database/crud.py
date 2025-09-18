"""
Shared CRUD Operations
Eliminates redundant CRUD patterns across all services.
"""

from typing import Generic, TypeVar, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime
from .base import HMSBaseModel

ModelType = TypeVar("ModelType", bound=HMSBaseModel)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseCRUD(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base CRUD operations class - eliminates redundant CRUD code."""

    def __init__(self, model: type[ModelType]):
        self.model = model

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """Get single record by ID."""
        return db.query(self.model).filter(self.model.id == id, self.model.is_active == True).first()

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        search: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        order_direction: str = "asc"
    ) -> List[ModelType]:
        """Get multiple records with filtering, search, and pagination."""
        query = db.query(self.model).filter(self.model.is_active == True)

        # Apply filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)

        # Apply search
        if search and search_fields:
            search_conditions = []
            for field in search_fields:
                if hasattr(self.model, field):
                    search_conditions.append(getattr(self.model, field).ilike(f"%{search}%"))
            if search_conditions:
                query = query.filter(or_(*search_conditions))

        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            if order_direction.lower() == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))
        else:
            # Default ordering by creation date
            query = query.order_by(desc(self.model.created_at))

        # Apply pagination
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: CreateSchemaType, created_by: Optional[str] = None) -> ModelType:
        """Create new record."""
        obj_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
        obj_data['created_by'] = created_by
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        db_obj: ModelType,
        obj_in: UpdateSchemaType,
        updated_by: Optional[str] = None
    ) -> ModelType:
        """Update existing record."""
        obj_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in
        obj_data['updated_by'] = updated_by

        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int, deleted_by: Optional[str] = None) -> Optional[ModelType]:
        """Soft delete record."""
        db_obj = self.get(db, id=id)
        if db_obj:
            db_obj.is_active = False
            db_obj.updated_by = deleted_by
            db.commit()
            db.refresh(db_obj)
        return db_obj

    def count(self, db: Session, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters."""
        query = db.query(self.model).filter(self.model.is_active == True)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)

        return query.count()

    def exists(self, db: Session, id: int) -> bool:
        """Check if record exists."""
        return db.query(self.model).filter(
            self.model.id == id,
            self.model.is_active == True
        ).first() is not None


class TimestampedCRUD(BaseCRUD[ModelType, CreateSchemaType, UpdateSchemaType]):
    """CRUD operations with timestamp management."""

    def get_by_date_range(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """Get records within date range."""
        return db.query(self.model).filter(
            and_(
                self.model.created_at >= start_date,
                self.model.created_at <= end_date,
                self.model.is_active == True
            )
        ).offset(skip).limit(limit).all()

    def get_recent(
        self,
        db: Session,
        hours: int = 24,
        limit: int = 100
    ) -> List[ModelType]:
        """Get recent records."""
        cutoff_time = datetime.utcnow()
        cutoff_time = cutoff_time.replace(hour=cutoff_time.hour - hours)

        return db.query(self.model).filter(
            and_(
                self.model.created_at >= cutoff_time,
                self.model.is_active == True
            )
        ).order_by(desc(self.model.created_at)).limit(limit).all()


class AuditedCRUD(TimestampedCRUD[ModelType, CreateSchemaType, UpdateSchemaType]):
    """CRUD operations with full audit trail."""

    def create_with_audit(
        self,
        db: Session,
        obj_in: CreateSchemaType,
        created_by: str,
        audit_details: Optional[Dict[str, Any]] = None
    ) -> ModelType:
        """Create record with audit trail."""
        obj = self.create(db, obj_in, created_by)

        # Create audit entry
        self._create_audit_entry(
            db=db,
            action="CREATE",
            entity_type=self.model.__name__,
            entity_id=str(obj.id),
            user=created_by,
            details=audit_details or obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
        )

        return obj

    def update_with_audit(
        self,
        db: Session,
        db_obj: ModelType,
        obj_in: UpdateSchemaType,
        updated_by: str,
        audit_details: Optional[Dict[str, Any]] = None
    ) -> ModelType:
        """Update record with audit trail."""
        old_data = db_obj.to_dict() if hasattr(db_obj, 'to_dict') else {}
        obj = self.update(db, db_obj, obj_in, updated_by)

        # Create audit entry
        self._create_audit_entry(
            db=db,
            action="UPDATE",
            entity_type=self.model.__name__,
            entity_id=str(obj.id),
            user=updated_by,
            details={
                "old_data": old_data,
                "new_data": obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in,
                "audit_details": audit_details
            }
        )

        return obj

    def delete_with_audit(
        self,
        db: Session,
        id: int,
        deleted_by: str,
        reason: Optional[str] = None
    ) -> Optional[ModelType]:
        """Soft delete record with audit trail."""
        obj = self.delete(db, id, deleted_by)

        if obj:
            self._create_audit_entry(
                db=db,
                action="DELETE",
                entity_type=self.model.__name__,
                entity_id=str(id),
                user=deleted_by,
                details={"reason": reason}
            )

        return obj

    def _create_audit_entry(
        self,
        db: Session,
        action: str,
        entity_type: str,
        entity_id: str,
        user: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Create audit entry (to be implemented by specific services)."""
        # This should be implemented in the specific service's audit model
        pass


# Common CRUD operations utility functions
def get_standard_filters(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract standard filters from request data."""
    filters = {}

    # Common filter fields
    filter_fields = ['status', 'is_active', 'created_by', 'updated_by']

    for field in filter_fields:
        if field in request_data:
            filters[field] = request_data[field]

    return filters


def get_pagination_params(skip: int = 0, limit: int = 100) -> tuple[int, int]:
    """Standard pagination parameters."""
    # Validate and enforce reasonable limits
    skip = max(0, skip)
    limit = min(1000, max(1, limit))  # Max 1000 records per request

    return skip, limit


def get_search_params(request_data: Dict[str, Any]) -> tuple[Optional[str], Optional[List[str]]]:
    """Extract search parameters from request data."""
    search = request_data.get('search')
    search_fields = request_data.get('search_fields')

    if search and not search_fields:
        # Default search fields if not specified
        search_fields = ['name', 'description']

    return search, search_fields


def get_ordering_params(request_data: Dict[str, Any]) -> tuple[Optional[str], str]:
    """Extract ordering parameters from request data."""
    order_by = request_data.get('order_by')
    order_direction = request_data.get('order_direction', 'asc')

    # Validate order direction
    if order_direction.lower() not in ['asc', 'desc']:
        order_direction = 'asc'

    return order_by, order_direction