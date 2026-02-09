import enum
from datetime import date
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Date, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TenantMixin, TimestampMixin


class RegulationEnum(enum.Enum):
    """Regulation types."""
    ITAR = "ITAR"
    EAR = "EAR"
    DFARS = "DFARS"
    BERRY = "BERRY"
    BAA = "BAA"


class ComplianceStatusEnum(enum.Enum):
    """Compliance status."""
    compliant = "compliant"
    non_compliant = "non_compliant"
    pending = "pending"
    exempt = "exempt"


class ComplianceRecord(Base, TenantMixin, TimestampMixin):
    """Compliance record model."""

    __tablename__ = "compliance_records"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    supplier_id: Mapped[UUID] = mapped_column(
        ForeignKey("suppliers.id"),
        nullable=False,
        index=True
    )

    regulation: Mapped[RegulationEnum] = mapped_column(nullable=False)
    status: Mapped[ComplianceStatusEnum] = mapped_column(nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(
        JSONB().with_variant(JSON, "sqlite"), nullable=True
    )

    verified_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    verified_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )
