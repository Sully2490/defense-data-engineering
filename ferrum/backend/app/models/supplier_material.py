from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class SupplierMaterial(Base, TimestampMixin):
    """Junction table for supplier-material relationship."""

    __tablename__ = "supplier_materials"

    org_id: Mapped[UUID] = mapped_column(primary_key=True, index=True)
    supplier_id: Mapped[UUID] = mapped_column(
        ForeignKey("suppliers.id"),
        primary_key=True,
        index=True
    )
    material_id: Mapped[UUID] = mapped_column(
        ForeignKey("materials.id"),
        primary_key=True,
        index=True
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    lead_time_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    min_order_qty: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
