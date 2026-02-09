#!/usr/bin/env python3
"""
Seed database with initial reference data and sample suppliers/materials.

Usage:
    python -m data.scripts.seed_db
"""

import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

# Add backend to path for imports
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.config import get_settings
from app.models import (
    Base,
    Organization,
    User,
    RoleEnum,
    MaterialCategory,
    Capability,
    Certification,
    Material,
    Supplier,
    SupplierCapability,
    ProficiencyEnum,
    SupplierCertification,
    CertificationStatusEnum,
    SupplierMaterial,
    Price,
    ComplianceRecord,
    RegulationEnum,
    ComplianceStatusEnum,
)
from app.core.security import hash_password


# Paths
DATA_DIR = Path(__file__).parent.parent
SEED_DIR = DATA_DIR / "seed"
SCHEMAS_DIR = DATA_DIR / "schemas"


def load_csv(filename: str) -> List[Dict[str, Any]]:
    """Load CSV file and return list of dicts."""
    filepath = SEED_DIR / filename
    if not filepath.exists():
        print(f"Warning: {filepath} not found, skipping...")
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def validate_schema(data: List[Dict], schema_file: str) -> bool:
    """Validate data against JSON schema (optional, warns on failure)."""
    schema_path = SCHEMAS_DIR / schema_file
    if not schema_path.exists():
        print(f"Warning: Schema {schema_file} not found, skipping validation")
        return True

    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        # Basic validation - just check required fields exist
        if data and 'required' in schema:
            for row in data[:5]:  # Check first 5 rows
                for field in schema['required']:
                    if field not in row:
                        print(f"Warning: Required field '{field}' missing in {schema_file}")
                        return False
        print(f"✓ Schema validation passed for {schema_file}")
        return True
    except Exception as e:
        print(f"Warning: Schema validation error for {schema_file}: {e}")
        return True  # Continue anyway


def str_to_bool(value: str) -> bool:
    """Convert string to boolean."""
    if isinstance(value, bool):
        return value
    return value.lower() in ('true', '1', 'yes', 'y')


def safe_float(value: str, default: float = 0.0) -> float:
    """Safely convert string to float."""
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default


def safe_int(value: str, default: int = 0) -> int:
    """Safely convert string to int."""
    try:
        return int(value) if value else default
    except (ValueError, TypeError):
        return default


def safe_date(value: str) -> Optional[datetime]:
    """Safely parse date string."""
    if not value or value.strip() == '':
        return None
    try:
        return datetime.strptime(value.strip(), '%Y-%m-%d')
    except ValueError:
        return None


def seed_organization(session: Session) -> Organization:
    """Create seed organization."""
    print("\n=== Creating Seed Organization ===")

    org = session.execute(
        select(Organization).where(Organization.name == "Ferrum Demo Org")
    ).scalar_one_or_none()

    if org:
        print(f"✓ Organization already exists: {org.name}")
        return org

    org = Organization(
        name="Ferrum Demo Org",
        tier="enterprise",
        settings={"demo": True}
    )
    session.add(org)
    session.commit()
    session.refresh(org)

    print(f"✓ Created organization: {org.name} (ID: {org.id})")
    return org


def seed_admin_user(session: Session, org: Organization) -> User:
    """Create seed admin user."""
    print("\n=== Creating Seed Admin User ===")

    user = session.execute(
        select(User).where(User.email == "admin@ferrum.dev")
    ).scalar_one_or_none()

    if user:
        print(f"✓ Admin user already exists: {user.email}")
        return user

    user = User(
        email="admin@ferrum.dev",
        hashed_password=hash_password("ferrum123"),
        full_name="Ferrum Admin",
        role=RoleEnum.org_admin,
        is_active=True,
        org_id=org.id
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    print(f"✓ Created admin user: {user.email}")
    print(f"  Password: ferrum123")
    print(f"  Role: {user.role.value}")
    return user


def seed_material_categories(session: Session) -> Dict[str, MaterialCategory]:
    """Seed material categories with hierarchy."""
    print("\n=== Seeding Material Categories ===")

    rows = load_csv("material_categories.csv")
    validate_schema(rows, "material_schema.json")

    categories = {}
    # First pass: create all categories without parents
    for row in rows:
        name = row['name']
        existing = session.execute(
            select(MaterialCategory).where(MaterialCategory.name == name)
        ).scalar_one_or_none()

        if existing:
            categories[name] = existing
            continue

        cat = MaterialCategory(
            name=name,
            slug=row['slug']
        )
        session.add(cat)
        categories[name] = cat

    session.commit()

    # Second pass: set parent relationships
    for row in rows:
        if row['parent_name']:
            cat = categories[row['name']]
            parent = categories.get(row['parent_name'])
            if parent:
                cat.parent_id = parent.id

    session.commit()

    print(f"✓ Seeded {len(categories)} material categories")
    return categories


def seed_capabilities(session: Session) -> Dict[str, Capability]:
    """Seed capabilities."""
    print("\n=== Seeding Capabilities ===")

    rows = load_csv("capabilities.csv")
    capabilities = {}

    for row in rows:
        name = row['name']
        existing = session.execute(
            select(Capability).where(Capability.name == name)
        ).scalar_one_or_none()

        if existing:
            capabilities[name] = existing
            continue

        cap = Capability(
            name=name,
            category=row['category'],
            slug=row['slug']
        )
        session.add(cap)
        capabilities[name] = cap

    session.commit()
    print(f"✓ Seeded {len(capabilities)} capabilities")
    return capabilities


def seed_certifications(session: Session) -> Dict[str, Certification]:
    """Seed certifications."""
    print("\n=== Seeding Certifications ===")

    rows = load_csv("certifications.csv")
    certifications = {}

    for row in rows:
        name = row['name']
        existing = session.execute(
            select(Certification).where(Certification.name == name)
        ).scalar_one_or_none()

        if existing:
            certifications[name] = existing
            continue

        cert = Certification(
            name=name,
            issuing_body=row['body'],
            category=row['category'],
            slug=row['slug']
        )
        session.add(cert)
        certifications[name] = cert

    session.commit()
    print(f"✓ Seeded {len(certifications)} certifications")
    return certifications


def seed_materials(session: Session, org: Organization, categories: Dict[str, MaterialCategory]) -> Dict[str, Material]:
    """Seed materials."""
    print("\n=== Seeding Materials ===")

    rows = load_csv("materials.csv")
    validate_schema(rows, "material_schema.json")

    materials = {}

    for row in rows:
        name = row['name']
        existing = session.execute(
            select(Material).where(
                Material.name == name,
                Material.org_id == org.id
            )
        ).scalar_one_or_none()

        if existing:
            materials[name] = existing
            continue

        category = categories.get(row['category_name'])
        if not category:
            print(f"Warning: Category '{row['category_name']}' not found for material '{name}'")
            continue

        material = Material(
            name=name,
            category_id=category.id,
            specification=row.get('specification', ''),
            grade=row.get('grade', ''),
            form=row.get('form', ''),
            material_type=row.get('material_type', ''),
            nsn=row.get('nsn') if row.get('nsn') else None,
            specialty_metal=str_to_bool(row.get('specialty_metal', 'false')),
            domestic_required=str_to_bool(row.get('domestic_required', 'false')),
            export_controlled=str_to_bool(row.get('export_controlled', 'false')),
            org_id=org.id
        )
        session.add(material)
        materials[name] = material

    session.commit()
    print(f"✓ Seeded {len(materials)} materials")
    return materials


def seed_suppliers(session: Session, org: Organization) -> Dict[str, Supplier]:
    """Seed suppliers."""
    print("\n=== Seeding Suppliers ===")

    rows = load_csv("suppliers.csv")
    validate_schema(rows, "supplier_schema.json")

    suppliers = {}

    for row in rows:
        name = row['name']
        existing = session.execute(
            select(Supplier).where(
                Supplier.name == name,
                Supplier.org_id == org.id
            )
        ).scalar_one_or_none()

        if existing:
            suppliers[name] = existing
            continue

        supplier = Supplier(
            name=name,
            cage_code=row.get('cage_code'),
            sam_uei=row.get('sam_uei'),
            duns_number=row.get('duns_number'),
            address=row.get('address', ''),
            city=row.get('city', ''),
            state=row.get('state', ''),
            zip_code=row.get('zip', ''),
            country=row.get('country', 'USA'),
            naics_codes=[code.strip() for code in row.get('naics_codes', '').split(',') if code.strip()],
            website=row.get('website'),
            contact_email=row.get('contact_email'),
            contact_phone=row.get('contact_phone'),
            small_business=str_to_bool(row.get('small_business', 'false')),
            woman_owned=str_to_bool(row.get('woman_owned', 'false')),
            veteran_owned=str_to_bool(row.get('veteran_owned', 'false')),
            hub_zone=str_to_bool(row.get('hub_zone', 'false')),
            risk_score=safe_float(row.get('risk_score', '0.0')),
            contains_cui=str_to_bool(row.get('contains_cui', 'false')),
            description=row.get('description', ''),
            org_id=org.id
        )
        session.add(supplier)
        suppliers[name] = supplier

    session.commit()
    print(f"✓ Seeded {len(suppliers)} suppliers")
    return suppliers


def seed_supplier_capabilities(
    session: Session,
    suppliers: Dict[str, Supplier],
    capabilities: Dict[str, Capability]
):
    """Seed supplier-capability relationships."""
    print("\n=== Seeding Supplier Capabilities ===")

    rows = load_csv("supplier_capabilities.csv")
    count = 0

    proficiency_map = {
        'beginner': ProficiencyEnum.beginner,
        'intermediate': ProficiencyEnum.intermediate,
        'advanced': ProficiencyEnum.advanced,
        'expert': ProficiencyEnum.expert
    }

    for row in rows:
        supplier = suppliers.get(row['supplier_name'])
        capability = capabilities.get(row['capability_name'])

        if not supplier or not capability:
            continue

        existing = session.execute(
            select(SupplierCapability).where(
                SupplierCapability.supplier_id == supplier.id,
                SupplierCapability.capability_id == capability.id
            )
        ).scalar_one_or_none()

        if existing:
            continue

        proficiency = proficiency_map.get(row.get('proficiency', 'intermediate').lower(), ProficiencyEnum.intermediate)

        sc = SupplierCapability(
            supplier_id=supplier.id,
            capability_id=capability.id,
            proficiency=proficiency
        )
        session.add(sc)
        count += 1

    session.commit()
    print(f"✓ Seeded {count} supplier-capability relationships")


def seed_supplier_certifications(
    session: Session,
    suppliers: Dict[str, Supplier],
    certifications: Dict[str, Certification]
):
    """Seed supplier-certification relationships."""
    print("\n=== Seeding Supplier Certifications ===")

    rows = load_csv("supplier_certifications.csv")
    count = 0

    status_map = {
        'active': CertificationStatusEnum.active,
        'expired': CertificationStatusEnum.expired,
        'pending': CertificationStatusEnum.pending,
        'suspended': CertificationStatusEnum.suspended
    }

    for row in rows:
        supplier = suppliers.get(row['supplier_name'])
        certification = certifications.get(row['certification_name'])

        if not supplier or not certification:
            continue

        existing = session.execute(
            select(SupplierCertification).where(
                SupplierCertification.supplier_id == supplier.id,
                SupplierCertification.certification_id == certification.id,
                SupplierCertification.cert_number == row.get('cert_number', '')
            )
        ).scalar_one_or_none()

        if existing:
            continue

        status = status_map.get(row.get('status', 'active').lower(), CertificationStatusEnum.active)

        sc = SupplierCertification(
            supplier_id=supplier.id,
            certification_id=certification.id,
            cert_number=row.get('cert_number', ''),
            issued_date=safe_date(row.get('issued_date')),
            expiry_date=safe_date(row.get('expiry_date')),
            status=status
        )
        session.add(sc)
        count += 1

    session.commit()
    print(f"✓ Seeded {count} supplier-certification relationships")


def seed_supplier_materials(
    session: Session,
    suppliers: Dict[str, Supplier],
    materials: Dict[str, Material]
):
    """Seed supplier-material relationships."""
    print("\n=== Seeding Supplier Materials ===")

    rows = load_csv("supplier_materials.csv")
    count = 0

    for row in rows:
        supplier = suppliers.get(row['supplier_name'])
        material = materials.get(row['material_name'])

        if not supplier or not material:
            continue

        existing = session.execute(
            select(SupplierMaterial).where(
                SupplierMaterial.supplier_id == supplier.id,
                SupplierMaterial.material_id == material.id
            )
        ).scalar_one_or_none()

        if existing:
            continue

        sm = SupplierMaterial(
            supplier_id=supplier.id,
            material_id=material.id,
            is_primary=str_to_bool(row.get('is_primary', 'false')),
            lead_time_days=safe_int(row.get('lead_time_days', '0')),
            min_order_qty=safe_int(row.get('min_order_qty', '1'))
        )
        session.add(sm)
        count += 1

    session.commit()
    print(f"✓ Seeded {count} supplier-material relationships")


def seed_prices(
    session: Session,
    suppliers: Dict[str, Supplier],
    materials: Dict[str, Material]
):
    """Seed price data."""
    print("\n=== Seeding Prices ===")

    rows = load_csv("prices.csv")
    count = 0

    for row in rows:
        supplier = suppliers.get(row['supplier_name'])
        material = materials.get(row['material_name'])

        if not supplier or not material:
            continue

        price = Price(
            supplier_id=supplier.id,
            material_id=material.id,
            price=safe_float(row.get('price', '0.0')),
            currency=row.get('currency', 'USD'),
            unit=row.get('unit', 'each'),
            quantity_min=safe_int(row.get('quantity_min', '1')),
            quantity_max=safe_int(row.get('quantity_max')) if row.get('quantity_max') else None,
            effective_date=safe_date(row.get('effective_date')) or datetime.now(),
            expiry_date=safe_date(row.get('expiry_date'))
        )
        session.add(price)
        count += 1

    session.commit()
    print(f"✓ Seeded {count} price entries")


def seed_compliance_records(session: Session, suppliers: Dict[str, Supplier]):
    """Seed compliance records."""
    print("\n=== Seeding Compliance Records ===")

    rows = load_csv("compliance_records.csv")
    count = 0

    regulation_map = {
        'ITAR': RegulationEnum.itar,
        'EAR': RegulationEnum.ear,
        'DFARS': RegulationEnum.dfars,
        'BERRY': RegulationEnum.berry,
        'BAA': RegulationEnum.baa,
        'NIST 800-171': RegulationEnum.nist_800_171
    }

    status_map = {
        'compliant': ComplianceStatusEnum.compliant,
        'non_compliant': ComplianceStatusEnum.non_compliant,
        'under_review': ComplianceStatusEnum.under_review,
        'not_applicable': ComplianceStatusEnum.not_applicable
    }

    for row in rows:
        supplier = suppliers.get(row['supplier_name'])

        if not supplier:
            continue

        regulation = regulation_map.get(row.get('regulation', ''))
        if not regulation:
            continue

        existing = session.execute(
            select(ComplianceRecord).where(
                ComplianceRecord.supplier_id == supplier.id,
                ComplianceRecord.regulation == regulation
            )
        ).scalar_one_or_none()

        if existing:
            continue

        status = status_map.get(row.get('status', 'compliant').lower(), ComplianceStatusEnum.compliant)

        cr = ComplianceRecord(
            supplier_id=supplier.id,
            regulation=regulation,
            status=status,
            details=row.get('details', '')
        )
        session.add(cr)
        count += 1

    session.commit()
    print(f"✓ Seeded {count} compliance records")


def main():
    """Main seeding function."""
    print("=" * 60)
    print("FERRUM DATABASE SEEDING")
    print("=" * 60)

    # Get database URL
    settings = get_settings()
    db_url = settings.DATABASE_URL_SYNC

    print(f"\nConnecting to: {db_url.split('@')[-1]}")  # Hide password

    # Create sync engine
    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    with SessionLocal() as session:
        try:
            # Seed in order
            org = seed_organization(session)
            admin = seed_admin_user(session, org)
            categories = seed_material_categories(session)
            capabilities = seed_capabilities(session)
            certifications = seed_certifications(session)
            materials = seed_materials(session, org, categories)
            suppliers = seed_suppliers(session, org)
            seed_supplier_capabilities(session, suppliers, capabilities)
            seed_supplier_certifications(session, suppliers, certifications)
            seed_supplier_materials(session, suppliers, materials)
            seed_prices(session, suppliers, materials)
            seed_compliance_records(session, suppliers)

            print("\n" + "=" * 60)
            print("SEEDING COMPLETE")
            print("=" * 60)
            print(f"\nSummary:")
            print(f"  Organization: {org.name}")
            print(f"  Admin User: {admin.email} (password: ferrum123)")
            print(f"  Material Categories: {len(categories)}")
            print(f"  Capabilities: {len(capabilities)}")
            print(f"  Certifications: {len(certifications)}")
            print(f"  Materials: {len(materials)}")
            print(f"  Suppliers: {len(suppliers)}")
            print("\nNext steps:")
            print("  1. Run: python -m data.scripts.sync_graph")
            print("  2. Run: python -m data.scripts.generate_embeddings")
            print("  3. Start the API: uvicorn app.main:app --reload")

        except Exception as e:
            print(f"\n✗ Error during seeding: {e}")
            import traceback
            traceback.print_exc()
            session.rollback()
            sys.exit(1)


if __name__ == "__main__":
    main()
