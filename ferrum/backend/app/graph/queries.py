"""Graph query service for common supply chain graph queries."""

import logging
from typing import Any, Optional
from uuid import UUID

from .client import Neo4jClient

logger = logging.getLogger(__name__)


class GraphQueryService:
    """Service class for executing common graph queries."""

    def __init__(self, client: Neo4jClient):
        """Initialize GraphQueryService with a Neo4jClient.

        Args:
            client: Connected Neo4jClient instance
        """
        self.client = client

    async def find_alternative_suppliers(
        self,
        supplier_id: UUID,
        material_id: UUID,
        org_id: UUID
    ) -> list[dict[str, Any]]:
        """Find alternative suppliers for a specific material.

        Args:
            supplier_id: Current supplier UUID
            material_id: Material UUID to find alternatives for
            org_id: Organization UUID for tenant filtering

        Returns:
            List of alternative supplier dictionaries
        """
        query = """
        MATCH (s:Supplier {id: $sid})-[:SUPPLIES]->(m:Material {id: $mid})
        MATCH (alt:Supplier)-[:SUPPLIES]->(m)
        WHERE alt.org_id = $org_id AND alt.id <> $sid
        RETURN alt {
            .id,
            .name,
            .cage_code,
            .country,
            .risk_score,
            .small_business,
            .woman_owned,
            .veteran_owned
        } as supplier
        ORDER BY alt.risk_score ASC, alt.name ASC
        """

        params = {
            "sid": str(supplier_id),
            "mid": str(material_id),
            "org_id": str(org_id)
        }

        try:
            records = await self.client.execute_read(query, params)
            alternatives = [record["supplier"] for record in records]
            logger.info(
                f"Found {len(alternatives)} alternative suppliers for "
                f"material {material_id}"
            )
            return alternatives
        except Exception as e:
            logger.error(f"Error finding alternative suppliers: {e}")
            return []

    async def detect_single_source_risks(
        self,
        org_id: UUID
    ) -> list[dict[str, Any]]:
        """Detect materials with only one supplier (single-source risk).

        Args:
            org_id: Organization UUID for tenant filtering

        Returns:
            List of dictionaries containing material and sole supplier info
        """
        query = """
        MATCH (m:Material)<-[:SUPPLIES]-(s:Supplier)
        WHERE s.org_id = $org_id
        WITH m, collect(s) as suppliers
        WHERE size(suppliers) = 1
        RETURN m {
            .id,
            .name,
            .specification,
            .nsn,
            .specialty_metal,
            .domestic_required,
            .export_controlled
        } as material,
        suppliers[0] {
            .id,
            .name,
            .cage_code,
            .country,
            .risk_score
        } as sole_supplier
        ORDER BY m.name ASC
        """

        params = {"org_id": str(org_id)}

        try:
            records = await self.client.execute_read(query, params)
            logger.info(
                f"Found {len(records)} single-source materials for org {org_id}"
            )
            return records
        except Exception as e:
            logger.error(f"Error detecting single-source risks: {e}")
            return []

    async def get_supply_chain_path(
        self,
        supplier_id: UUID,
        depth: int = 3
    ) -> list[dict[str, Any]]:
        """Get full supply chain graph from a supplier up to specified depth.

        Args:
            supplier_id: Starting supplier UUID
            depth: Maximum relationship depth (default: 3)

        Returns:
            List of path dictionaries representing the supply chain
        """
        query = f"""
        MATCH path = (s:Supplier {{id: $sid}})-[*1..{depth}]->()
        RETURN path
        LIMIT 1000
        """

        params = {"sid": str(supplier_id)}

        try:
            records = await self.client.execute_read(query, params)
            logger.info(
                f"Retrieved {len(records)} supply chain paths for "
                f"supplier {supplier_id}"
            )
            return records
        except Exception as e:
            logger.error(f"Error getting supply chain path: {e}")
            return []

    async def get_bom_tree(
        self,
        bom_root_id: UUID
    ) -> list[dict[str, Any]]:
        """Get Bill of Materials tree traversal from root item.

        Args:
            bom_root_id: Root BOM item UUID

        Returns:
            List of path dictionaries representing the BOM hierarchy
        """
        query = """
        MATCH path = (root:BOMItem {id: $rid})-[:CONTAINS*]->(child)
        RETURN path
        ORDER BY length(path) ASC
        """

        params = {"rid": str(bom_root_id)}

        try:
            records = await self.client.execute_read(query, params)
            logger.info(
                f"Retrieved {len(records)} BOM paths from root {bom_root_id}"
            )
            return records
        except Exception as e:
            logger.error(f"Error getting BOM tree: {e}")
            return []

    async def get_geopolitical_risk(
        self,
        country: str
    ) -> list[dict[str, Any]]:
        """Get suppliers and materials at risk from a specific country.

        Args:
            country: Country name to analyze

        Returns:
            List of supplier dictionaries headquartered in the country
        """
        query = """
        MATCH (s:Supplier)-[:HEADQUARTERED_IN]->(c:Country)
        WHERE c.name = $country
        RETURN s {
            .id,
            .name,
            .cage_code,
            .country,
            .risk_score,
            .address,
            .city,
            .state
        } as supplier,
        c.name as country
        ORDER BY s.risk_score DESC, s.name ASC
        """

        params = {"country": country}

        try:
            records = await self.client.execute_read(query, params)
            suppliers = [record["supplier"] for record in records]
            logger.info(
                f"Found {len(suppliers)} suppliers at risk in {country}"
            )
            return suppliers
        except Exception as e:
            logger.error(f"Error getting geopolitical risk: {e}")
            return []

    async def get_supplier_network(
        self,
        supplier_id: UUID
    ) -> dict[str, list[dict[str, Any]]]:
        """Get all relationships for a supplier.

        Retrieves capabilities, certifications, materials, and regulations
        associated with a supplier.

        Args:
            supplier_id: Supplier UUID

        Returns:
            Dictionary with relationship types as keys and related nodes as values
        """
        query = """
        MATCH (s:Supplier {id: $sid})-[r]->(n)
        RETURN type(r) as relationship_type,
               labels(n) as node_labels,
               properties(n) as node_properties
        ORDER BY relationship_type, node_properties.name
        """

        params = {"sid": str(supplier_id)}

        try:
            records = await self.client.execute_read(query, params)

            # Organize results by relationship type
            network = {
                "capabilities": [],
                "certifications": [],
                "materials": [],
                "regulations": [],
                "other": []
            }

            for record in records:
                rel_type = record["relationship_type"]
                node_labels = record["node_labels"]
                node_props = record["node_properties"]

                if "Capability" in node_labels:
                    network["capabilities"].append(node_props)
                elif "Certification" in node_labels:
                    network["certifications"].append(node_props)
                elif "Material" in node_labels:
                    network["materials"].append(node_props)
                elif "Regulation" in node_labels:
                    network["regulations"].append(node_props)
                else:
                    network["other"].append({
                        "type": rel_type,
                        "labels": node_labels,
                        "properties": node_props
                    })

            logger.info(
                f"Retrieved supplier network for {supplier_id}: "
                f"{len(network['capabilities'])} capabilities, "
                f"{len(network['certifications'])} certifications, "
                f"{len(network['materials'])} materials"
            )
            return network
        except Exception as e:
            logger.error(f"Error getting supplier network: {e}")
            return {
                "capabilities": [],
                "certifications": [],
                "materials": [],
                "regulations": [],
                "other": []
            }
