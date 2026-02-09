# Ferrum Data Directory

Seed data, JSON schemas, and database import scripts for the Ferrum defense data engineering platform.

## Directory Structure

```
data/
├── seed/              # Seed CSV files
├── schemas/           # JSON Schema validation files
├── scripts/           # Database seeding and sync scripts
└── README.md          # This file
```

## Seed Data Files

### Reference Data
- `capabilities.csv` - 30 manufacturing capabilities (CNC machining, welding, composites, etc.)
- `certifications.csv` - 25 industry certifications (AS9100D, ITAR, NADCAP, etc.)
- `material_categories.csv` - Hierarchical material categories

### Core Data
- `materials.csv` - 200 defense/aerospace materials with specifications
  - Titanium alloys, aluminum alloys, specialty metals
  - Composites, polymers, ceramics, electronics
  - Fasteners, raw stock materials
  - NSN numbers, export control flags, specialty metal designations

- `suppliers.csv` - 50 representative defense suppliers
  - Realistic CAGE codes, SAM UEI, DUNS numbers
  - Geographic distribution across US states
  - Small business, woman-owned, veteran-owned designations
  - NAICS codes, risk scores, CUI handling flags

### Relationship Data
- `supplier_capabilities.csv` - Supplier-capability mappings (150+ rows)
- `supplier_certifications.csv` - Supplier certifications with dates (120+ rows)
- `supplier_materials.csv` - Supplier-material relationships (200+ rows)
- `prices.csv` - Material pricing by supplier (150+ rows)
- `compliance_records.csv` - ITAR/DFARS/EAR compliance status (100+ rows)

## JSON Schemas

- `supplier_schema.json` - Validates supplier CSV structure
- `material_schema.json` - Validates material CSV structure

Schemas include:
- Field type validation
- Pattern matching (CAGE codes, NSN, ZIP codes)
- Required field enforcement
- Enum validation for controlled vocabularies

## Scripts

### 1. Database Seeding (`seed_db.py`)

Seeds PostgreSQL database with all reference and sample data.

**Usage:**
```bash
cd /path/to/ferrum
python -m data.scripts.seed_db
```

**What it does:**
- Creates seed organization "Ferrum Demo Org"
- Creates admin user (admin@ferrum.dev / ferrum123)
- Loads all CSV files in dependency order
- Validates data against JSON schemas
- Handles duplicates gracefully
- Prints progress and summary

**Requirements:**
- PostgreSQL database running
- Database URL in `.env` file
- Alembic migrations applied

### 2. Graph Sync (`sync_graph.py`)

Syncs PostgreSQL data to Neo4j graph database.

**Usage:**
```bash
python -m data.scripts.sync_graph [--org-name "Ferrum Demo Org"]
```

**What it does:**
- Connects to PostgreSQL and Neo4j
- Syncs suppliers, materials, capabilities, certifications
- Creates graph relationships (SUPPLIES, HAS_CAPABILITY, etc.)
- Reports sync statistics

**Requirements:**
- Neo4j database running
- Neo4j credentials in `.env` file
- PostgreSQL seeded with data

### 3. Embedding Generation (`generate_embeddings.py`)

Generates embeddings for semantic search using OpenAI API.

**Usage:**
```bash
python -m data.scripts.generate_embeddings [--org-name "Ferrum Demo Org"] [--batch-size 100]
```

**What it does:**
- Fetches suppliers and materials from PostgreSQL
- Generates text representations (name + description + attributes)
- Chunks long text appropriately
- Calls OpenAI embeddings API in batches
- Stores embeddings in `document_embeddings` table

**Requirements:**
- OpenAI API key in `.env` file
- PostgreSQL seeded with data
- Network access to OpenAI API

**Options:**
- `--org-name`: Organization to process (default: "Ferrum Demo Org")
- `--batch-size`: Items per API batch (default: 100)

## Full Setup Workflow

1. **Setup environment:**
   ```bash
   cd ferrum/backend
   cp .env.example .env
   # Edit .env with database URLs and API keys
   ```

2. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

3. **Seed database:**
   ```bash
   cd ..
   python -m data.scripts.seed_db
   ```

4. **Sync to Neo4j:**
   ```bash
   python -m data.scripts.sync_graph
   ```

5. **Generate embeddings:**
   ```bash
   python -m data.scripts.generate_embeddings
   ```

6. **Start API:**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

## Data Quality

### CAGE Codes
- Format: 5 alphanumeric characters
- Example: `7K4M9`, `2H8T5`
- All CAGE codes in seed data are realistic but fictional

### NAICS Codes
- Real NAICS codes for defense/aerospace industries
- Common codes:
  - `332710` - Machine shops
  - `336413` - Aircraft parts manufacturing
  - `336414` - Guided missile and space vehicle manufacturing
  - `334419` - Electronics assembly

### NSN Numbers
- Format: `####-##-###-####`
- Example: `9515-01-234-5678`
- Fictional but properly formatted

### Specifications
- Real specification numbers:
  - AMS (Aerospace Material Specifications)
  - MIL-DTL (Military Detail Specifications)
  - ASTM (American Society for Testing and Materials)
  - ISO (International Organization for Standardization)

## Customization

### Adding More Suppliers
1. Add rows to `seed/suppliers.csv`
2. Follow existing format and patterns
3. Use realistic CAGE codes (5 chars, alphanumeric)
4. Include proper NAICS codes for industry
5. Re-run seed script

### Adding More Materials
1. Add rows to `seed/materials.csv`
2. Ensure category exists in `material_categories.csv`
3. Use proper specification numbers (AMS, MIL-DTL, etc.)
4. Set appropriate flags (specialty_metal, export_controlled, etc.)
5. Re-run seed script

### Modifying Relationships
- Edit `supplier_capabilities.csv`, `supplier_certifications.csv`, etc.
- Ensure referenced suppliers/materials exist
- Re-run seed script

## Troubleshooting

### "Organization not found"
- Check organization name matches exactly
- Run: `SELECT name FROM organizations;` in PostgreSQL
- Use `--org-name` flag to specify correct name

### "Schema validation failed"
- Check CSV format matches schema
- Ensure required fields are present
- Validate data types (booleans, numbers, dates)

### "Duplicate key error"
- Script handles duplicates by skipping
- To reset, drop and recreate database
- Or delete specific rows manually

### "OpenAI API error"
- Check API key is valid and has credits
- Reduce batch size if rate limited
- Check network connectivity

## Performance Notes

- **Seeding:** ~30-60 seconds for full dataset
- **Graph Sync:** ~1-2 minutes for 50 suppliers + 200 materials
- **Embeddings:** ~5-10 minutes depending on batch size and API rate limits

## Support

For issues or questions:
1. Check console output for specific error messages
2. Verify all prerequisites are met
3. Check `.env` file configuration
4. Review PostgreSQL and Neo4j logs
