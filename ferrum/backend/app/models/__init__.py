"""SQLAlchemy ORM models for Ferrum."""

from .base import Base, TenantMixin, TimestampMixin
from .organization import Organization, TierEnum
from .user import User, RoleEnum
from .supplier import Supplier
from .material import Material, MaterialCategory
from .capability import Capability, SupplierCapability, ProficiencyEnum
from .certification import Certification, SupplierCertification, CertificationStatusEnum
from .supplier_material import SupplierMaterial
from .price import Price
from .compliance import ComplianceRecord, RegulationEnum, ComplianceStatusEnum
from .bom import BomItem
from .audit import AuditLog
from .embedding import DocumentEmbedding

__all__ = [
    # Base classes
    "Base",
    "TenantMixin",
    "TimestampMixin",

    # Models
    "Organization",
    "User",
    "Supplier",
    "Material",
    "MaterialCategory",
    "Capability",
    "SupplierCapability",
    "Certification",
    "SupplierCertification",
    "SupplierMaterial",
    "Price",
    "ComplianceRecord",
    "BomItem",
    "AuditLog",
    "DocumentEmbedding",

    # Enums
    "TierEnum",
    "RoleEnum",
    "ProficiencyEnum",
    "CertificationStatusEnum",
    "RegulationEnum",
    "ComplianceStatusEnum",
]
