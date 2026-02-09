import enum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class TierEnum(enum.Enum):
    """Organization tier levels."""
    free = "free"
    pro = "pro"
    enterprise = "enterprise"


class Organization(Base, TimestampMixin):
    """Organization/tenant model."""

    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    tier: Mapped[TierEnum] = mapped_column(nullable=False, default=TierEnum.free)
    cui_authorized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
