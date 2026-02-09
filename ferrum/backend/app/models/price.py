from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TenantMixin, TimestampMixin


class Price(Base, TenantMixin, TimestampMixin):
    """Price model for supplier-material pricing."""

    __tablename__ = "prices"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    supplier_id: Mapped[UUID] = mapped_column(
        ForeignKey("suppliers.id"),
        nullable=False,
        index=True
    )
    material_id: Mapped[UUID] = mapped_column(
        ForeignKey("materials.id"),
        nullable=False,
        index=True
    )

    price: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    unit: Mapped[str] = mapped_column(String(50), nullable=False)

    # Quantity tiers
    quantity_min: Mapped[Optional[int]] = mapped_column(nullable=True)
    quantity_max: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Validity period
    effective_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
