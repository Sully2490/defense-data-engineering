from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import TSVECTOR as _TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TenantMixin, TimestampMixin


class MaterialCategory(Base, TimestampMixin):
    """Material category taxonomy (shared reference data)."""

    __tablename__ = "material_categories"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("material_categories.id"),
        nullable=True,
        index=True
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)


class Material(Base, TenantMixin, TimestampMixin):
    """Material model with multi-tenant support."""

    __tablename__ = "materials"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    category_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("material_categories.id"),
        nullable=True,
        index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    specification: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    grade: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    form: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    material_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    nsn: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Regulatory flags
    specialty_metal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    domestic_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    export_controlled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Full-text search
    search_vector: Mapped[Optional[str]] = mapped_column(
        _TSVECTOR().with_variant(Text, "sqlite"), nullable=True
    )
