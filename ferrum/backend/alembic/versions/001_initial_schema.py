"""Initial database schema with RLS policies.

Revision ID: 001
Revises:
Create Date: 2026-02-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables, indexes, and RLS policies."""

    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create organizations table (no RLS - global reference)
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('tier', sa.String(50), nullable=False),
        sa.Column('cui_authorized', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_organizations_slug', 'organizations', ['slug'])

    # Create users table (RLS by org_id)
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('cui_clearance', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_users_org_id', 'users', ['org_id'])
    op.create_index('ix_users_email', 'users', ['email'])

    # Create material_categories table (no RLS - global reference)
    op.create_table(
        'material_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('material_categories.id'), nullable=True),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_material_categories_parent_id', 'material_categories', ['parent_id'])
    op.create_index('ix_material_categories_slug', 'material_categories', ['slug'])

    # Create capabilities table (no RLS - global reference)
    op.create_table(
        'capabilities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
    )
    op.create_index('ix_capabilities_slug', 'capabilities', ['slug'])

    # Create certifications table (no RLS - global reference)
    op.create_table(
        'certifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('body', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
    )
    op.create_index('ix_certifications_slug', 'certifications', ['slug'])

    # Create suppliers table (RLS by org_id)
    op.create_table(
        'suppliers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cage_code', sa.String(50), nullable=True),
        sa.Column('sam_uei', sa.String(50), nullable=True),
        sa.Column('duns_number', sa.String(50), nullable=True),
        sa.Column('address', sa.String(255), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(50), nullable=True),
        sa.Column('zip_code', sa.String(20), nullable=True),
        sa.Column('country', sa.String(100), nullable=False, default='USA'),
        sa.Column('naics_codes', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('contact_phone', sa.String(50), nullable=True),
        sa.Column('small_business', sa.Boolean(), nullable=False, default=False),
        sa.Column('woman_owned', sa.Boolean(), nullable=False, default=False),
        sa.Column('veteran_owned', sa.Boolean(), nullable=False, default=False),
        sa.Column('hub_zone', sa.Boolean(), nullable=False, default=False),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('contains_cui', sa.Boolean(), nullable=False, default=False),
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_suppliers_org_id', 'suppliers', ['org_id'])
    op.create_index('ix_suppliers_search_vector', 'suppliers', ['search_vector'], postgresql_using='gin')

    # Create materials table (RLS by org_id)
    op.create_table(
        'materials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('material_categories.id'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('specification', sa.String(255), nullable=True),
        sa.Column('grade', sa.String(100), nullable=True),
        sa.Column('form', sa.String(100), nullable=True),
        sa.Column('material_type', sa.String(100), nullable=True),
        sa.Column('nsn', sa.String(50), nullable=True),
        sa.Column('specialty_metal', sa.Boolean(), nullable=False, default=False),
        sa.Column('domestic_required', sa.Boolean(), nullable=False, default=False),
        sa.Column('export_controlled', sa.Boolean(), nullable=False, default=False),
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_materials_org_id', 'materials', ['org_id'])
    op.create_index('ix_materials_category_id', 'materials', ['category_id'])
    op.create_index('ix_materials_search_vector', 'materials', ['search_vector'], postgresql_using='gin')

    # Create supplier_capabilities table (composite primary key with org_id)
    op.create_table(
        'supplier_capabilities',
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('suppliers.id'), nullable=False),
        sa.Column('capability_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('capabilities.id'), nullable=False),
        sa.Column('proficiency', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('org_id', 'supplier_id', 'capability_id'),
    )
    op.create_index('ix_supplier_capabilities_org_id', 'supplier_capabilities', ['org_id'])
    op.create_index('ix_supplier_capabilities_supplier_id', 'supplier_capabilities', ['supplier_id'])
    op.create_index('ix_supplier_capabilities_capability_id', 'supplier_capabilities', ['capability_id'])

    # Create supplier_certifications table (composite primary key with org_id)
    op.create_table(
        'supplier_certifications',
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('suppliers.id'), nullable=False),
        sa.Column('certification_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('certifications.id'), nullable=False),
        sa.Column('cert_number', sa.String(100), nullable=True),
        sa.Column('issued_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('org_id', 'supplier_id', 'certification_id'),
    )
    op.create_index('ix_supplier_certifications_org_id', 'supplier_certifications', ['org_id'])
    op.create_index('ix_supplier_certifications_supplier_id', 'supplier_certifications', ['supplier_id'])
    op.create_index('ix_supplier_certifications_certification_id', 'supplier_certifications', ['certification_id'])

    # Create supplier_materials table (composite primary key with org_id)
    op.create_table(
        'supplier_materials',
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('suppliers.id'), nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('materials.id'), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, default=False),
        sa.Column('lead_time_days', sa.Integer(), nullable=True),
        sa.Column('min_order_qty', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('org_id', 'supplier_id', 'material_id'),
    )
    op.create_index('ix_supplier_materials_org_id', 'supplier_materials', ['org_id'])
    op.create_index('ix_supplier_materials_supplier_id', 'supplier_materials', ['supplier_id'])
    op.create_index('ix_supplier_materials_material_id', 'supplier_materials', ['material_id'])

    # Create prices table (RLS by org_id)
    op.create_table(
        'prices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('suppliers.id'), nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('materials.id'), nullable=False),
        sa.Column('price', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, default='USD'),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('quantity_min', sa.Integer(), nullable=True),
        sa.Column('quantity_max', sa.Integer(), nullable=True),
        sa.Column('effective_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_prices_org_id', 'prices', ['org_id'])
    op.create_index('ix_prices_supplier_id', 'prices', ['supplier_id'])
    op.create_index('ix_prices_material_id', 'prices', ['material_id'])

    # Create compliance_records table (RLS by org_id)
    op.create_table(
        'compliance_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('suppliers.id'), nullable=False),
        sa.Column('regulation', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('verified_date', sa.Date(), nullable=True),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_compliance_records_org_id', 'compliance_records', ['org_id'])
    op.create_index('ix_compliance_records_supplier_id', 'compliance_records', ['supplier_id'])
    op.create_index('ix_compliance_records_verified_by', 'compliance_records', ['verified_by'])

    # Create bom_items table (RLS by org_id)
    op.create_table(
        'bom_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bom_items.id'), nullable=True),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('materials.id'), nullable=False),
        sa.Column('part_number', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_bom_items_org_id', 'bom_items', ['org_id'])
    op.create_index('ix_bom_items_parent_id', 'bom_items', ['parent_id'])
    op.create_index('ix_bom_items_material_id', 'bom_items', ['material_id'])

    # Create audit_logs table (no RLS - global audit trail)
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('cui_accessed', sa.Boolean(), nullable=False, default=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_audit_logs_org_id', 'audit_logs', ['org_id'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_resource_id', 'audit_logs', ['resource_id'])
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])

    # Create document_embeddings table (RLS by org_id)
    op.create_table(
        'document_embeddings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False, default=0),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_document_embeddings_org_id', 'document_embeddings', ['org_id'])
    op.create_index('ix_document_embeddings_source_type', 'document_embeddings', ['source_type'])
    op.create_index('ix_document_embeddings_source_id', 'document_embeddings', ['source_id'])

    # Create vector index for embeddings using ivfflat
    # Note: This requires data to be present, so it should be created after initial data load
    # op.execute("CREATE INDEX ix_document_embeddings_embedding ON document_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)")

    # Enable Row-Level Security on tenant-scoped tables
    tenant_tables = [
        'users',
        'suppliers',
        'materials',
        'supplier_capabilities',
        'supplier_certifications',
        'supplier_materials',
        'prices',
        'compliance_records',
        'bom_items',
        'document_embeddings',
    ]

    for table in tenant_tables:
        # Enable RLS
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")

        # Create SELECT policy
        op.execute(f"""
            CREATE POLICY {table}_select_policy ON {table}
            FOR SELECT
            USING (org_id = current_setting('app.current_org_id', true)::uuid)
        """)

        # Create INSERT policy
        op.execute(f"""
            CREATE POLICY {table}_insert_policy ON {table}
            FOR INSERT
            WITH CHECK (org_id = current_setting('app.current_org_id', true)::uuid)
        """)

        # Create UPDATE policy
        op.execute(f"""
            CREATE POLICY {table}_update_policy ON {table}
            FOR UPDATE
            USING (org_id = current_setting('app.current_org_id', true)::uuid)
            WITH CHECK (org_id = current_setting('app.current_org_id', true)::uuid)
        """)

        # Create DELETE policy
        op.execute(f"""
            CREATE POLICY {table}_delete_policy ON {table}
            FOR DELETE
            USING (org_id = current_setting('app.current_org_id', true)::uuid)
        """)


def downgrade() -> None:
    """Drop all tables and policies."""

    # Drop RLS policies
    tenant_tables = [
        'users',
        'suppliers',
        'materials',
        'supplier_capabilities',
        'supplier_certifications',
        'supplier_materials',
        'prices',
        'compliance_records',
        'bom_items',
        'document_embeddings',
    ]

    for table in tenant_tables:
        op.execute(f"DROP POLICY IF EXISTS {table}_select_policy ON {table}")
        op.execute(f"DROP POLICY IF EXISTS {table}_insert_policy ON {table}")
        op.execute(f"DROP POLICY IF EXISTS {table}_update_policy ON {table}")
        op.execute(f"DROP POLICY IF EXISTS {table}_delete_policy ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    # Drop tables in reverse order
    op.drop_table('document_embeddings')
    op.drop_table('audit_logs')
    op.drop_table('bom_items')
    op.drop_table('compliance_records')
    op.drop_table('prices')
    op.drop_table('supplier_materials')
    op.drop_table('supplier_certifications')
    op.drop_table('supplier_capabilities')
    op.drop_table('materials')
    op.drop_table('suppliers')
    op.drop_table('certifications')
    op.drop_table('capabilities')
    op.drop_table('material_categories')
    op.drop_table('users')
    op.drop_table('organizations')

    # Drop extension
    op.execute("DROP EXTENSION IF EXISTS vector")
