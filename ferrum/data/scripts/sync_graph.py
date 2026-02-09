#!/usr/bin/env python3
"""
Sync PostgreSQL data to Neo4j graph database.

Usage:
    python -m data.scripts.sync_graph [--org-name "Ferrum Demo Org"]
"""

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Add backend to path for imports
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.config import get_settings
from app.models import Organization
from app.graph.client import Neo4jClient
from app.graph.sync import GraphSync


async def main(org_name: str = "Ferrum Demo Org"):
    """Main sync function."""
    print("=" * 60)
    print("FERRUM GRAPH SYNC (PostgreSQL → Neo4j)")
    print("=" * 60)

    # Get settings
    settings = get_settings()

    print(f"\nConnecting to PostgreSQL: {settings.DATABASE_URL.split('@')[-1]}")
    print(f"Connecting to Neo4j: {settings.NEO4J_URI}")

    # Create async engine for PostgreSQL
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Connect to Neo4j
    neo4j_client = Neo4jClient(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD
    )

    try:
        async with AsyncSessionLocal() as session:
            # Find organization
            result = await session.execute(
                select(Organization).where(Organization.name == org_name)
            )
            org = result.scalar_one_or_none()

            if not org:
                print(f"\n✗ Organization '{org_name}' not found")
                print("Available organizations:")
                result = await session.execute(select(Organization))
                orgs = result.scalars().all()
                for o in orgs:
                    print(f"  - {o.name} (ID: {o.id})")
                sys.exit(1)

            print(f"\n=== Syncing Organization: {org.name} ===")
            print(f"Organization ID: {org.id}")

            # Create GraphSync instance
            graph_sync = GraphSync(neo4j_client, session)

            # Run full sync
            print("\nStarting sync...")
            stats = await graph_sync.sync_all(org.id)

            print("\n" + "=" * 60)
            print("SYNC COMPLETE")
            print("=" * 60)
            print(f"\nSynced to Neo4j:")
            print(f"  Countries: {stats.get('countries', 0)}")
            print(f"  Material Categories: {stats.get('material_categories', 0)}")
            print(f"  Suppliers: {stats.get('suppliers', 0)}")
            print(f"  Materials: {stats.get('materials', 0)}")
            print(f"  Capabilities: {stats.get('capabilities', 0)}")
            print(f"  Certifications: {stats.get('certifications', 0)}")
            print(f"  BOM Items: {stats.get('bom_items', 0)}")
            print(f"  Relationships: {stats.get('relationships', 0)}")

            print("\nNext steps:")
            print("  1. Run: python -m data.scripts.generate_embeddings")
            print("  2. Start the API: uvicorn app.main:app --reload")
            print("  3. Query Neo4j at: http://localhost:7474")

    except Exception as e:
        print(f"\n✗ Error during sync: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # Close Neo4j connection
        neo4j_client.close()
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync PostgreSQL to Neo4j")
    parser.add_argument(
        "--org-name",
        default="Ferrum Demo Org",
        help="Organization name to sync (default: Ferrum Demo Org)"
    )
    args = parser.parse_args()

    asyncio.run(main(args.org_name))
