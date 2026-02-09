import enum
from datetime import date
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class CertificationStatusEnum(enum.Enum):
    """Certification status."""
    active = "active"
    expired = "expired"
    suspended = "suspended"


class Certification(Base):
    """Certification reference data (shared across all orgs)."""

    __tablename__ = "certifications"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)


class SupplierCertification(Base, TimestampMixin):
    """Junction table for supplier-certification relationship."""

    __tablename__ = "supplier_certifications"

    org_id: Mapped[UUID] = mapped_column(primary_key=True, index=True)
    supplier_id: Mapped[UUID] = mapped_column(
        ForeignKey("suppliers.id"),
        primary_key=True,
        index=True
    )
    certification_id: Mapped[UUID] = mapped_column(
        ForeignKey("certifications.id"),
        primary_key=True,
        index=True
    )
    cert_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    issued_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[CertificationStatusEnum] = mapped_column(
        nullable=False,
        default=CertificationStatusEnum.active
    )
