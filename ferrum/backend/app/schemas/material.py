"""Material schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MaterialSupplierSchema(BaseModel):
    """Material supplier nested schema."""

    id: UUID
    name: str
    cage_code: Optional[str] = None

    model_config = {"from_attributes": True}


class MaterialCreate(BaseModel):
    """Schema for creating a material."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    specification: Optional[str] = None
    grade: Optional[str] = None
    form: Optional[str] = None
    material_type: Optional[str] = None
    nsn: Optional[str] = None
    specialty_metal: bool = False
    domestic_required: bool = False
    export_controlled: bool = False


class MaterialUpdate(BaseModel):
    """Schema for updating a material."""

    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    specification: Optional[str] = None
    grade: Optional[str] = None
    form: Optional[str] = None
    material_type: Optional[str] = None
    nsn: Optional[str] = None
    specialty_metal: Optional[bool] = None
    domestic_required: Optional[bool] = None
    export_controlled: Optional[bool] = None


class MaterialResponse(BaseModel):
    """Schema for material response."""

    id: UUID
    org_id: UUID
    name: str
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    specification: Optional[str] = None
    grade: Optional[str] = None
    form: Optional[str] = None
    material_type: Optional[str] = None
    nsn: Optional[str] = None
    specialty_metal: bool = False
    domestic_required: bool = False
    export_controlled: bool = False
    created_at: datetime
    updated_at: datetime
    suppliers: list[MaterialSupplierSchema] = []

    model_config = {"from_attributes": True}


class MaterialListResponse(BaseModel):
    """Paginated material list response."""

    items: list[MaterialResponse]
    total: int
    page: int
    size: int
    pages: int


class MaterialCategoryResponse(BaseModel):
    """Material category response."""

    id: UUID
    name: str
    slug: str
    parent_id: Optional[UUID] = None

    model_config = {"from_attributes": True}
