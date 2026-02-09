from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TenantMixin, TimestampMixin


class BomItem(Base, TenantMixin, TimestampMixin):
    """Bill of Materials (BOM) item model with hierarchical structure."""

    __tablename__ = "bom_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("bom_items.id"),
        nullable=True,
        index=True
    )
    material_id: Mapped[UUID] = mapped_column(
        ForeignKey("materials.id"),
        nullable=False,
        index=True
    )

    part_number: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=4), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
