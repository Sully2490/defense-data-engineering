#!/usr/bin/env python3
"""
Generate embeddings for suppliers and materials using OpenAI API.

Usage:
    python -m data.scripts.generate_embeddings [--org-name "Ferrum Demo Org"] [--batch-size 100]
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from openai import AsyncOpenAI

# Add backend to path for imports
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.config import get_settings
from app.models import Organization, Supplier, Material, DocumentEmbedding


EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536


def chunk_text(text: str, max_length: int = 8000) -> List[str]:
    """
    Chunk text into smaller pieces for embedding.

    Args:
        text: Input text
        max_length: Maximum characters per chunk

    Returns:
        List of text chunks
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    words = text.split()
    current_chunk = []
    current_length = 0

    for word in words:
        word_length = len(word) + 1  # +1 for space
        if current_length + word_length > max_length:
            if current_chunk:
                chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = word_length
        else:
            current_chunk.append(word)
            current_length += word_length

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


def prepare_supplier_text(supplier: Supplier) -> str:
    """
    Prepare supplier text for embedding.

    Args:
        supplier: Supplier instance

    Returns:
        Combined text representation
    """
    parts = [
        f"Name: {supplier.name}",
    ]

    if supplier.description:
        parts.append(f"Description: {supplier.description}")

    if supplier.city and supplier.state:
        parts.append(f"Location: {supplier.city}, {supplier.state}")

    if supplier.naics_codes:
        parts.append(f"NAICS Codes: {', '.join(supplier.naics_codes)}")

    attributes = []
    if supplier.small_business:
        attributes.append("Small Business")
    if supplier.woman_owned:
        attributes.append("Woman Owned")
    if supplier.veteran_owned:
        attributes.append("Veteran Owned")
    if supplier.hub_zone:
        attributes.append("HUBZone")

    if attributes:
        parts.append(f"Attributes: {', '.join(attributes)}")

    return '. '.join(parts)


def prepare_material_text(material: Material) -> str:
    """
    Prepare material text for embedding.

    Args:
        material: Material instance

    Returns:
        Combined text representation
    """
    parts = [
        f"Name: {material.name}",
    ]

    if material.specification:
        parts.append(f"Specification: {material.specification}")

    if material.grade:
        parts.append(f"Grade: {material.grade}")

    if material.form:
        parts.append(f"Form: {material.form}")

    if material.material_type:
        parts.append(f"Type: {material.material_type}")

    attributes = []
    if material.specialty_metal:
        attributes.append("Specialty Metal")
    if material.domestic_required:
        attributes.append("Domestic Sourcing Required")
    if material.export_controlled:
        attributes.append("Export Controlled")

    if attributes:
        parts.append(f"Attributes: {', '.join(attributes)}")

    if material.nsn:
        parts.append(f"NSN: {material.nsn}")

    return '. '.join(parts)


async def generate_embeddings_batch(
    client: AsyncOpenAI,
    texts: List[str]
) -> List[List[float]]:
    """
    Generate embeddings for a batch of texts.

    Args:
        client: OpenAI async client
        texts: List of texts to embed

    Returns:
        List of embedding vectors
    """
    response = await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )

    return [item.embedding for item in response.data]


async def process_suppliers(
    session: AsyncSession,
    openai_client: AsyncOpenAI,
    org_id: str,
    batch_size: int = 100
) -> int:
    """
    Generate and store embeddings for all suppliers.

    Args:
        session: Database session
        openai_client: OpenAI async client
        org_id: Organization ID
        batch_size: Number of items to process at once

    Returns:
        Number of embeddings generated
    """
    print("\n=== Processing Suppliers ===")

    # Fetch suppliers
    result = await session.execute(
        select(Supplier).where(Supplier.org_id == org_id)
    )
    suppliers = result.scalars().all()

    if not suppliers:
        print("No suppliers found")
        return 0

    print(f"Found {len(suppliers)} suppliers")

    count = 0
    for i in range(0, len(suppliers), batch_size):
        batch = suppliers[i:i + batch_size]
        texts = []
        metadata = []

        for supplier in batch:
            text = prepare_supplier_text(supplier)
            chunks = chunk_text(text)

            for chunk_idx, chunk in enumerate(chunks):
                texts.append(chunk)
                metadata.append({
                    "supplier_id": supplier.id,
                    "chunk_idx": chunk_idx,
                    "total_chunks": len(chunks)
                })

        # Generate embeddings
        print(f"Generating embeddings for batch {i // batch_size + 1} ({len(texts)} chunks)...")
        embeddings = await generate_embeddings_batch(openai_client, texts)

        # Store in database
        for text, embedding, meta in zip(texts, embeddings, metadata):
            # Check if embedding already exists
            existing = await session.execute(
                select(DocumentEmbedding).where(
                    DocumentEmbedding.entity_type == "supplier",
                    DocumentEmbedding.entity_id == meta["supplier_id"],
                    DocumentEmbedding.chunk_index == meta["chunk_idx"]
                )
            )
            if existing.scalar_one_or_none():
                continue

            doc_embedding = DocumentEmbedding(
                entity_type="supplier",
                entity_id=meta["supplier_id"],
                content=text,
                embedding=embedding,
                chunk_index=meta["chunk_idx"],
                metadata_={"total_chunks": meta["total_chunks"]}
            )
            session.add(doc_embedding)
            count += 1

        await session.commit()

    print(f"✓ Generated {count} supplier embeddings")
    return count


async def process_materials(
    session: AsyncSession,
    openai_client: AsyncOpenAI,
    org_id: str,
    batch_size: int = 100
) -> int:
    """
    Generate and store embeddings for all materials.

    Args:
        session: Database session
        openai_client: OpenAI async client
        org_id: Organization ID
        batch_size: Number of items to process at once

    Returns:
        Number of embeddings generated
    """
    print("\n=== Processing Materials ===")

    # Fetch materials
    result = await session.execute(
        select(Material).where(Material.org_id == org_id)
    )
    materials = result.scalars().all()

    if not materials:
        print("No materials found")
        return 0

    print(f"Found {len(materials)} materials")

    count = 0
    for i in range(0, len(materials), batch_size):
        batch = materials[i:i + batch_size]
        texts = []
        metadata = []

        for material in batch:
            text = prepare_material_text(material)
            chunks = chunk_text(text)

            for chunk_idx, chunk in enumerate(chunks):
                texts.append(chunk)
                metadata.append({
                    "material_id": material.id,
                    "chunk_idx": chunk_idx,
                    "total_chunks": len(chunks)
                })

        # Generate embeddings
        print(f"Generating embeddings for batch {i // batch_size + 1} ({len(texts)} chunks)...")
        embeddings = await generate_embeddings_batch(openai_client, texts)

        # Store in database
        for text, embedding, meta in zip(texts, embeddings, metadata):
            # Check if embedding already exists
            existing = await session.execute(
                select(DocumentEmbedding).where(
                    DocumentEmbedding.entity_type == "material",
                    DocumentEmbedding.entity_id == meta["material_id"],
                    DocumentEmbedding.chunk_index == meta["chunk_idx"]
                )
            )
            if existing.scalar_one_or_none():
                continue

            doc_embedding = DocumentEmbedding(
                entity_type="material",
                entity_id=meta["material_id"],
                content=text,
                embedding=embedding,
                chunk_index=meta["chunk_idx"],
                metadata_={"total_chunks": meta["total_chunks"]}
            )
            session.add(doc_embedding)
            count += 1

        await session.commit()

    print(f"✓ Generated {count} material embeddings")
    return count


async def main(org_name: str = "Ferrum Demo Org", batch_size: int = 100):
    """Main embedding generation function."""
    print("=" * 60)
    print("FERRUM EMBEDDING GENERATION")
    print("=" * 60)

    # Get settings
    settings = get_settings()

    if not settings.OPENAI_API_KEY:
        print("\n✗ OPENAI_API_KEY not set in environment")
        print("Please set OPENAI_API_KEY in your .env file")
        sys.exit(1)

    print(f"\nConnecting to PostgreSQL: {settings.DATABASE_URL.split('@')[-1]}")
    print(f"Using OpenAI model: {EMBEDDING_MODEL}")

    # Create async engine for PostgreSQL
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Create OpenAI client
    openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

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

            print(f"\n=== Generating Embeddings for: {org.name} ===")
            print(f"Organization ID: {org.id}")
            print(f"Batch size: {batch_size}")

            # Generate embeddings
            supplier_count = await process_suppliers(
                session, openai_client, org.id, batch_size
            )
            material_count = await process_materials(
                session, openai_client, org.id, batch_size
            )

            print("\n" + "=" * 60)
            print("EMBEDDING GENERATION COMPLETE")
            print("=" * 60)
            print(f"\nGenerated embeddings:")
            print(f"  Suppliers: {supplier_count}")
            print(f"  Materials: {material_count}")
            print(f"  Total: {supplier_count + material_count}")

            print("\nNext steps:")
            print("  1. Start the API: uvicorn app.main:app --reload")
            print("  2. Test semantic search in the UI")
            print("  3. Try the AI chat interface")

    except Exception as e:
        print(f"\n✗ Error during embedding generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate embeddings for Ferrum data")
    parser.add_argument(
        "--org-name",
        default="Ferrum Demo Org",
        help="Organization name to process (default: Ferrum Demo Org)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of items to process per batch (default: 100)"
    )
    args = parser.parse_args()

    asyncio.run(main(args.org_name, args.batch_size))
