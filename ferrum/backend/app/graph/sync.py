"""Graph sync service for syncing PostgreSQL data to Neo4j."""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bom import BomItem
from app.models.capability import Capability, SupplierCapability
from app.models.certification import Certification, SupplierCertification
from app.models.compliance import ComplianceRecord
from app.models.material import Material, MaterialCategory
from app.models.supplier import Supplier
from app.models.supplier_material import SupplierMaterial

from .client import Neo4jClient

logger = logging.getLogger(__name__)


class GraphSync:
    """Service for syncing PostgreSQL data to Neo4j graph database."""

    def __init__(self, client: Neo4jClient, db_session: AsyncSession):
        """Initialize GraphSync with Neo4j client and database session.

        Args:
            client: Connected Neo4jClient instance
            db_session: Async SQLAlchemy session
        """
        self.client = client
        self.db_session = db_session

    async def sync_all(self, org_id: UUID) -> dict[str, int]:
        """Orchestrate full PostgreSQL to Neo4j sync for an organization.

        Args:
            org_id: Organization UUID to sync

        Returns:
            Dictionary with counts of synced entities
        """
        logger.info(f"Starting full sync for organization {org_id}")

        stats = {
            "suppliers": 0,
            "materials": 0,
            "material_categories": 0,
            "capabilities": 0,
            "certifications": 0,
            "countries": 0,
            "bom_items": 0,
            "relationships": 0
        }

        try:
            # Sync reference data first (no org filtering)
            stats["countries"] = await self.sync_countries()
            stats["material_categories"] = await self.sync_material_categories()

            # Sync org-specific nodes
            stats["suppliers"] = await self.sync_suppliers(org_id)
            stats["materials"] = await self.sync_materials(org_id)
            stats["capabilities"] = await self.sync_capabilities(org_id)
            stats["certifications"] = await self.sync_certifications(org_id)
            stats["bom_items"] = await self.sync_bom_items(org_id)

            # Sync relationships last
            stats["relationships"] = await self.sync_relationships(org_id)

            logger.info(f"Full sync completed for org {org_id}: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error during full sync for org {org_id}: {e}")
            raise

    async def sync_suppliers(self, org_id: UUID) -> int:
        """Sync supplier nodes from PostgreSQL to Neo4j.

        Args:
            org_id: Organization UUID

        Returns:
            Number of suppliers synced
        """
        query = select(Supplier).where(Supplier.org_id == org_id)
        result = await self.db_session.execute(query)
        suppliers = result.scalars().all()

        if not suppliers:
            logger.info(f"No suppliers found for org {org_id}")
            return 0

        # Convert to list of dicts for UNWIND
        supplier_data = [
            {
                "id": str(s.id),
                "org_id": str(s.org_id),
                "name": s.name,
                "description": s.description,
                "cage_code": s.cage_code,
                "sam_uei": s.sam_uei,
                "duns_number": s.duns_number,
                "address": s.address,
                "city": s.city,
                "state": s.state,
                "zip_code": s.zip_code,
                "country": s.country,
                "naics_codes": s.naics_codes or [],
                "website": s.website,
                "contact_email": s.contact_email,
                "contact_phone": s.contact_phone,
                "small_business": s.small_business,
                "woman_owned": s.woman_owned,
                "veteran_owned": s.veteran_owned,
                "hub_zone": s.hub_zone,
                "risk_score": s.risk_score,
                "contains_cui": s.contains_cui
            }
            for s in suppliers
        ]

        cypher = """
        UNWIND $suppliers as supplier
        MERGE (s:Supplier {id: supplier.id})
        SET s.org_id = supplier.org_id,
            s.name = supplier.name,
            s.description = supplier.description,
            s.cage_code = supplier.cage_code,
            s.sam_uei = supplier.sam_uei,
            s.duns_number = supplier.duns_number,
            s.address = supplier.address,
            s.city = supplier.city,
            s.state = supplier.state,
            s.zip_code = supplier.zip_code,
            s.country = supplier.country,
            s.naics_codes = supplier.naics_codes,
            s.website = supplier.website,
            s.contact_email = supplier.contact_email,
            s.contact_phone = supplier.contact_phone,
            s.small_business = supplier.small_business,
            s.woman_owned = supplier.woman_owned,
            s.veteran_owned = supplier.veteran_owned,
            s.hub_zone = supplier.hub_zone,
            s.risk_score = supplier.risk_score,
            s.contains_cui = supplier.contains_cui
        RETURN count(s) as count
        """

        result = await self.client.execute_write(cypher, {"suppliers": supplier_data})
        count = result[0]["count"] if result else 0
        logger.info(f"Synced {count} suppliers for org {org_id}")
        return count

    async def sync_materials(self, org_id: UUID) -> int:
        """Sync material nodes from PostgreSQL to Neo4j.

        Args:
            org_id: Organization UUID

        Returns:
            Number of materials synced
        """
        query = select(Material).where(Material.org_id == org_id)
        result = await self.db_session.execute(query)
        materials = result.scalars().all()

        if not materials:
            logger.info(f"No materials found for org {org_id}")
            return 0

        material_data = [
            {
                "id": str(m.id),
                "org_id": str(m.org_id),
                "category_id": str(m.category_id) if m.category_id else None,
                "name": m.name,
                "description": m.description,
                "specification": m.specification,
                "grade": m.grade,
                "form": m.form,
                "material_type": m.material_type,
                "nsn": m.nsn,
                "specialty_metal": m.specialty_metal,
                "domestic_required": m.domestic_required,
                "export_controlled": m.export_controlled
            }
            for m in materials
        ]

        cypher = """
        UNWIND $materials as material
        MERGE (m:Material {id: material.id})
        SET m.org_id = material.org_id,
            m.category_id = material.category_id,
            m.name = material.name,
            m.description = material.description,
            m.specification = material.specification,
            m.grade = material.grade,
            m.form = material.form,
            m.material_type = material.material_type,
            m.nsn = material.nsn,
            m.specialty_metal = material.specialty_metal,
            m.domestic_required = material.domestic_required,
            m.export_controlled = material.export_controlled
        RETURN count(m) as count
        """

        result = await self.client.execute_write(cypher, {"materials": material_data})
        count = result[0]["count"] if result else 0
        logger.info(f"Synced {count} materials for org {org_id}")
        return count

    async def sync_material_categories(self) -> int:
        """Sync material category nodes (reference data, no org filtering).

        Returns:
            Number of categories synced
        """
        query = select(MaterialCategory)
        result = await self.db_session.execute(query)
        categories = result.scalars().all()

        if not categories:
            logger.info("No material categories found")
            return 0

        category_data = [
            {
                "id": str(c.id),
                "name": c.name,
                "parent_id": str(c.parent_id) if c.parent_id else None,
                "slug": c.slug
            }
            for c in categories
        ]

        cypher = """
        UNWIND $categories as cat
        MERGE (c:MaterialCategory {id: cat.id})
        SET c.name = cat.name,
            c.parent_id = cat.parent_id,
            c.slug = cat.slug
        RETURN count(c) as count
        """

        result = await self.client.execute_write(cypher, {"categories": category_data})
        count = result[0]["count"] if result else 0
        logger.info(f"Synced {count} material categories")
        return count

    async def sync_capabilities(self, org_id: UUID) -> int:
        """Sync capability nodes (reference data, no org filtering).

        Note: Capabilities are shared across orgs, but we only sync those
        actually used by suppliers in this org.

        Args:
            org_id: Organization UUID

        Returns:
            Number of capabilities synced
        """
        # Get capabilities used by this org's suppliers
        query = (
            select(Capability)
            .join(SupplierCapability)
            .where(SupplierCapability.org_id == org_id)
            .distinct()
        )
        result = await self.db_session.execute(query)
        capabilities = result.scalars().all()

        if not capabilities:
            logger.info(f"No capabilities found for org {org_id}")
            return 0

        capability_data = [
            {
                "id": str(c.id),
                "name": c.name,
                "category": c.category,
                "slug": c.slug
            }
            for c in capabilities
        ]

        cypher = """
        UNWIND $capabilities as cap
        MERGE (c:Capability {id: cap.id})
        SET c.name = cap.name,
            c.category = cap.category,
            c.slug = cap.slug
        RETURN count(c) as count
        """

        result = await self.client.execute_write(
            cypher,
            {"capabilities": capability_data}
        )
        count = result[0]["count"] if result else 0
        logger.info(f"Synced {count} capabilities for org {org_id}")
        return count

    async def sync_certifications(self, org_id: UUID) -> int:
        """Sync certification nodes (reference data, no org filtering).

        Note: Certifications are shared across orgs, but we only sync those
        actually held by suppliers in this org.

        Args:
            org_id: Organization UUID

        Returns:
            Number of certifications synced
        """
        # Get certifications held by this org's suppliers
        query = (
            select(Certification)
            .join(SupplierCertification)
            .where(SupplierCertification.org_id == org_id)
            .distinct()
        )
        result = await self.db_session.execute(query)
        certifications = result.scalars().all()

        if not certifications:
            logger.info(f"No certifications found for org {org_id}")
            return 0

        certification_data = [
            {
                "id": str(c.id),
                "name": c.name,
                "body": c.body,
                "category": c.category,
                "slug": c.slug
            }
            for c in certifications
        ]

        cypher = """
        UNWIND $certifications as cert
        MERGE (c:Certification {id: cert.id})
        SET c.name = cert.name,
            c.body = cert.body,
            c.category = cert.category,
            c.slug = cert.slug
        RETURN count(c) as count
        """

        result = await self.client.execute_write(
            cypher,
            {"certifications": certification_data}
        )
        count = result[0]["count"] if result else 0
        logger.info(f"Synced {count} certifications for org {org_id}")
        return count

    async def sync_bom_items(self, org_id: UUID) -> int:
        """Sync BOM item nodes from PostgreSQL to Neo4j.

        Args:
            org_id: Organization UUID

        Returns:
            Number of BOM items synced
        """
        query = select(BomItem).where(BomItem.org_id == org_id)
        result = await self.db_session.execute(query)
        bom_items = result.scalars().all()

        if not bom_items:
            logger.info(f"No BOM items found for org {org_id}")
            return 0

        bom_data = [
            {
                "id": str(b.id),
                "org_id": str(b.org_id),
                "parent_id": str(b.parent_id) if b.parent_id else None,
                "material_id": str(b.material_id),
                "part_number": b.part_number,
                "description": b.description,
                "quantity": float(b.quantity),
                "unit": b.unit,
                "level": b.level
            }
            for b in bom_items
        ]

        cypher = """
        UNWIND $bom_items as bom
        MERGE (b:BOMItem {id: bom.id})
        SET b.org_id = bom.org_id,
            b.parent_id = bom.parent_id,
            b.material_id = bom.material_id,
            b.part_number = bom.part_number,
            b.description = bom.description,
            b.quantity = bom.quantity,
            b.unit = bom.unit,
            b.level = bom.level
        RETURN count(b) as count
        """

        result = await self.client.execute_write(cypher, {"bom_items": bom_data})
        count = result[0]["count"] if result else 0
        logger.info(f"Synced {count} BOM items for org {org_id}")
        return count

    async def sync_countries(self) -> int:
        """Sync country nodes from supplier locations.

        Returns:
            Number of countries synced
        """
        # Get distinct countries from suppliers
        query = select(Supplier.country).distinct()
        result = await self.db_session.execute(query)
        countries = [row[0] for row in result.all() if row[0]]

        if not countries:
            logger.info("No countries found in supplier data")
            return 0

        country_data = [{"name": country} for country in countries]

        cypher = """
        UNWIND $countries as country
        MERGE (c:Country {name: country.name})
        RETURN count(c) as count
        """

        result = await self.client.execute_write(cypher, {"countries": country_data})
        count = result[0]["count"] if result else 0
        logger.info(f"Synced {count} countries")
        return count

    async def sync_relationships(self, org_id: UUID) -> int:
        """Create edges between nodes.

        Creates the following relationships:
        - SUPPLIES: Supplier -> Material
        - HAS_CAPABILITY: Supplier -> Capability
        - HOLDS_CERTIFICATION: Supplier -> Certification
        - CONTAINS: BOMItem -> BOMItem (parent-child)
        - HEADQUARTERED_IN: Supplier -> Country
        - SUBJECT_TO: Supplier -> Regulation (from compliance records)
        - BELONGS_TO: Material -> MaterialCategory

        Args:
            org_id: Organization UUID

        Returns:
            Total number of relationships created
        """
        total_count = 0

        # SUPPLIES relationships (Supplier -> Material)
        query = select(SupplierMaterial).where(SupplierMaterial.org_id == org_id)
        result = await self.db_session.execute(query)
        supplier_materials = result.scalars().all()

        if supplier_materials:
            sm_data = [
                {
                    "supplier_id": str(sm.supplier_id),
                    "material_id": str(sm.material_id),
                    "is_primary": sm.is_primary,
                    "lead_time_days": sm.lead_time_days,
                    "min_order_qty": sm.min_order_qty
                }
                for sm in supplier_materials
            ]

            cypher = """
            UNWIND $relationships as rel
            MATCH (s:Supplier {id: rel.supplier_id})
            MATCH (m:Material {id: rel.material_id})
            MERGE (s)-[r:SUPPLIES]->(m)
            SET r.is_primary = rel.is_primary,
                r.lead_time_days = rel.lead_time_days,
                r.min_order_qty = rel.min_order_qty
            RETURN count(r) as count
            """

            result = await self.client.execute_write(
                cypher,
                {"relationships": sm_data}
            )
            count = result[0]["count"] if result else 0
            total_count += count
            logger.info(f"Created {count} SUPPLIES relationships")

        # HAS_CAPABILITY relationships (Supplier -> Capability)
        query = select(SupplierCapability).where(SupplierCapability.org_id == org_id)
        result = await self.db_session.execute(query)
        supplier_capabilities = result.scalars().all()

        if supplier_capabilities:
            sc_data = [
                {
                    "supplier_id": str(sc.supplier_id),
                    "capability_id": str(sc.capability_id),
                    "proficiency": sc.proficiency.value
                }
                for sc in supplier_capabilities
            ]

            cypher = """
            UNWIND $relationships as rel
            MATCH (s:Supplier {id: rel.supplier_id})
            MATCH (c:Capability {id: rel.capability_id})
            MERGE (s)-[r:HAS_CAPABILITY]->(c)
            SET r.proficiency = rel.proficiency
            RETURN count(r) as count
            """

            result = await self.client.execute_write(
                cypher,
                {"relationships": sc_data}
            )
            count = result[0]["count"] if result else 0
            total_count += count
            logger.info(f"Created {count} HAS_CAPABILITY relationships")

        # HOLDS_CERTIFICATION relationships (Supplier -> Certification)
        query = select(SupplierCertification).where(
            SupplierCertification.org_id == org_id
        )
        result = await self.db_session.execute(query)
        supplier_certifications = result.scalars().all()

        if supplier_certifications:
            sc_data = [
                {
                    "supplier_id": str(sc.supplier_id),
                    "certification_id": str(sc.certification_id),
                    "cert_number": sc.cert_number,
                    "issued_date": sc.issued_date.isoformat() if sc.issued_date else None,
                    "expiry_date": sc.expiry_date.isoformat() if sc.expiry_date else None,
                    "status": sc.status.value
                }
                for sc in supplier_certifications
            ]

            cypher = """
            UNWIND $relationships as rel
            MATCH (s:Supplier {id: rel.supplier_id})
            MATCH (c:Certification {id: rel.certification_id})
            MERGE (s)-[r:HOLDS_CERTIFICATION]->(c)
            SET r.cert_number = rel.cert_number,
                r.issued_date = rel.issued_date,
                r.expiry_date = rel.expiry_date,
                r.status = rel.status
            RETURN count(r) as count
            """

            result = await self.client.execute_write(
                cypher,
                {"relationships": sc_data}
            )
            count = result[0]["count"] if result else 0
            total_count += count
            logger.info(f"Created {count} HOLDS_CERTIFICATION relationships")

        # CONTAINS relationships (BOMItem parent -> child)
        query = select(BomItem).where(
            BomItem.org_id == org_id,
            BomItem.parent_id.isnot(None)
        )
        result = await self.db_session.execute(query)
        bom_items = result.scalars().all()

        if bom_items:
            bom_data = [
                {
                    "parent_id": str(b.parent_id),
                    "child_id": str(b.id),
                    "quantity": float(b.quantity),
                    "unit": b.unit
                }
                for b in bom_items
            ]

            cypher = """
            UNWIND $relationships as rel
            MATCH (parent:BOMItem {id: rel.parent_id})
            MATCH (child:BOMItem {id: rel.child_id})
            MERGE (parent)-[r:CONTAINS]->(child)
            SET r.quantity = rel.quantity,
                r.unit = rel.unit
            RETURN count(r) as count
            """

            result = await self.client.execute_write(
                cypher,
                {"relationships": bom_data}
            )
            count = result[0]["count"] if result else 0
            total_count += count
            logger.info(f"Created {count} CONTAINS relationships")

        # HEADQUARTERED_IN relationships (Supplier -> Country)
        query = select(Supplier).where(Supplier.org_id == org_id)
        result = await self.db_session.execute(query)
        suppliers = result.scalars().all()

        if suppliers:
            hq_data = [
                {
                    "supplier_id": str(s.id),
                    "country": s.country
                }
                for s in suppliers if s.country
            ]

            cypher = """
            UNWIND $relationships as rel
            MATCH (s:Supplier {id: rel.supplier_id})
            MATCH (c:Country {name: rel.country})
            MERGE (s)-[r:HEADQUARTERED_IN]->(c)
            RETURN count(r) as count
            """

            result = await self.client.execute_write(
                cypher,
                {"relationships": hq_data}
            )
            count = result[0]["count"] if result else 0
            total_count += count
            logger.info(f"Created {count} HEADQUARTERED_IN relationships")

        # SUBJECT_TO relationships (Supplier -> Regulation, from compliance records)
        query = select(ComplianceRecord).where(ComplianceRecord.org_id == org_id)
        result = await self.db_session.execute(query)
        compliance_records = result.scalars().all()

        if compliance_records:
            # First, ensure regulation nodes exist
            regulations = list(set(cr.regulation.value for cr in compliance_records))
            reg_data = [{"name": reg} for reg in regulations]

            reg_cypher = """
            UNWIND $regulations as reg
            MERGE (r:Regulation {name: reg.name})
            RETURN count(r) as count
            """

            await self.client.execute_write(reg_cypher, {"regulations": reg_data})

            # Then create relationships
            comp_data = [
                {
                    "supplier_id": str(cr.supplier_id),
                    "regulation": cr.regulation.value,
                    "status": cr.status.value,
                    "verified_date": cr.verified_date.isoformat() if cr.verified_date else None
                }
                for cr in compliance_records
            ]

            cypher = """
            UNWIND $relationships as rel
            MATCH (s:Supplier {id: rel.supplier_id})
            MATCH (r:Regulation {name: rel.regulation})
            MERGE (s)-[rel_edge:SUBJECT_TO]->(r)
            SET rel_edge.status = rel.status,
                rel_edge.verified_date = rel.verified_date
            RETURN count(rel_edge) as count
            """

            result = await self.client.execute_write(
                cypher,
                {"relationships": comp_data}
            )
            count = result[0]["count"] if result else 0
            total_count += count
            logger.info(f"Created {count} SUBJECT_TO relationships")

        # BELONGS_TO relationships (Material -> MaterialCategory)
        query = select(Material).where(
            Material.org_id == org_id,
            Material.category_id.isnot(None)
        )
        result = await self.db_session.execute(query)
        materials = result.scalars().all()

        if materials:
            cat_data = [
                {
                    "material_id": str(m.id),
                    "category_id": str(m.category_id)
                }
                for m in materials
            ]

            cypher = """
            UNWIND $relationships as rel
            MATCH (m:Material {id: rel.material_id})
            MATCH (c:MaterialCategory {id: rel.category_id})
            MERGE (m)-[r:BELONGS_TO]->(c)
            RETURN count(r) as count
            """

            result = await self.client.execute_write(
                cypher,
                {"relationships": cat_data}
            )
            count = result[0]["count"] if result else 0
            total_count += count
            logger.info(f"Created {count} BELONGS_TO relationships")

        logger.info(f"Total relationships created: {total_count}")
        return total_count
