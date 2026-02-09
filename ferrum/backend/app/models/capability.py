import enum
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class ProficiencyEnum(enum.Enum):
    """Capability proficiency levels."""
    basic = "basic"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"


class Capability(Base):
    """Capability reference data (shared across all orgs)."""

    __tablename__ = "capabilities"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)


class SupplierCapability(Base, TimestampMixin):
    """Junction table for supplier-capability relationship."""

    __tablename__ = "supplier_capabilities"

    org_id: Mapped[UUID] = mapped_column(primary_key=True, index=True)
    supplier_id: Mapped[UUID] = mapped_column(
        ForeignKey("suppliers.id"),
        primary_key=True,
        index=True
    )
    capability_id: Mapped[UUID] = mapped_column(
        ForeignKey("capabilities.id"),
        primary_key=True,
        index=True
    )
    proficiency: Mapped[ProficiencyEnum] = mapped_column(
        nullable=False,
        default=ProficiencyEnum.basic
    )
