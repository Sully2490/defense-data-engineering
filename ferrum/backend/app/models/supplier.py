from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import ARRAY, Boolean, Float, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TenantMixin, TimestampMixin


class Supplier(Base, TenantMixin, TimestampMixin):
    """Supplier model with multi-tenant support."""

    __tablename__ = "suppliers"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Government identifiers
    cage_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sam_uei: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    duns_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Address
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="USA")

    # Industry codes
    naics_codes: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String).with_variant(JSON, "sqlite"), nullable=True
    )

    # Contact
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Business classifications
    small_business: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    woman_owned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    veteran_owned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    hub_zone: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Risk and compliance
    risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    contains_cui: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Full-text search
    search_vector: Mapped[Optional[str]] = mapped_column(
        TSVECTOR().with_variant(Text, "sqlite"), nullable=True
    )

    __table_args__ = (
        {"schema": None}
    )
