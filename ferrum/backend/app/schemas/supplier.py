"""Supplier schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SupplierCapabilitySchema(BaseModel):
    """Supplier capability nested schema."""

    id: UUID
    name: str
    category: Optional[str] = None
    proficiency: Optional[str] = None

    model_config = {"from_attributes": True}


class SupplierCertificationSchema(BaseModel):
    """Supplier certification nested schema."""

    id: UUID
    name: str
    body: Optional[str] = None
    cert_number: Optional[str] = None
    issued_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    status: Optional[str] = None

    model_config = {"from_attributes": True}


class SupplierMaterialSchema(BaseModel):
    """Supplier material nested schema."""

    id: UUID
    name: str
    specification: Optional[str] = None

    model_config = {"from_attributes": True}


class SupplierCreate(BaseModel):
    """Schema for creating a supplier."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    cage_code: Optional[str] = Field(None, max_length=5)
    sam_uei: Optional[str] = None
    duns_number: Optional[str] = Field(None, max_length=9)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str = "US"
    naics_codes: Optional[list[str]] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    small_business: bool = False
    woman_owned: bool = False
    veteran_owned: bool = False
    hub_zone: bool = False
    risk_score: Optional[float] = None
    contains_cui: bool = False


class SupplierUpdate(BaseModel):
    """Schema for updating a supplier."""

    name: Optional[str] = None
    description: Optional[str] = None
    cage_code: Optional[str] = None
    sam_uei: Optional[str] = None
    duns_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    naics_codes: Optional[list[str]] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    small_business: Optional[bool] = None
    woman_owned: Optional[bool] = None
    veteran_owned: Optional[bool] = None
    hub_zone: Optional[bool] = None
    risk_score: Optional[float] = None
    contains_cui: Optional[bool] = None


class SupplierResponse(BaseModel):
    """Schema for supplier response with nested relations."""

    id: UUID
    org_id: UUID
    name: str
    description: Optional[str] = None
    cage_code: Optional[str] = None
    sam_uei: Optional[str] = None
    duns_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    naics_codes: Optional[list[str]] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    small_business: bool = False
    woman_owned: bool = False
    veteran_owned: bool = False
    hub_zone: bool = False
    risk_score: Optional[float] = None
    contains_cui: bool = False
    created_at: datetime
    updated_at: datetime
    capabilities: list[SupplierCapabilitySchema] = []
    certifications: list[SupplierCertificationSchema] = []
    materials: list[SupplierMaterialSchema] = []

    model_config = {"from_attributes": True}


class SupplierListResponse(BaseModel):
    """Paginated supplier list response."""

    items: list[SupplierResponse]
    total: int
    page: int
    size: int
    pages: int


class SupplierFilters(BaseModel):
    """Supplier filtering parameters."""

    naics_code: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    small_business: Optional[bool] = None
    certification: Optional[str] = None
    capability: Optional[str] = None
    search_query: Optional[str] = None
