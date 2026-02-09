# Defense Data Engineering

Defense and government data pipelines for contract tracking, procurement analysis, and federal spending intelligence.

## Projects

| # | Project | Description |
|---|---------|-------------|
| 01 | [Contract Pipeline](./01-contract-pipeline) | SAM.gov and DoD contract ingestion, normalization, and tracking |
| 02 | [Procurement Analysis](./02-procurement-analysis) | Federal spending data aggregation and analysis |
| -- | [Ferrum](./ferrum) | AI-powered supply chain intelligence platform for defense & robotics |

## Ferrum — Supply Chain Intelligence

Ferrum is a commercial SaaS product that helps procurement teams, supply chain analysts, and program managers discover suppliers, map risks, track pricing, and verify compliance across the full robotics/defense bill-of-materials.

**Key Features:**
- AI-powered natural language supplier search (Claude + pgvector RAG)
- Supply chain graph mapping (Neo4j)
- Multi-tenant with Row-Level Security
- Defense compliance tracking (ITAR, DFARS, Berry Amendment, BAA)
- CUI-aware access controls and audit logging

**Tech Stack:** FastAPI, Next.js 14, PostgreSQL + pgvector, Neo4j, Claude AI, Docker

**Quick Start:**
```bash
cd ferrum
cp .env.example .env
make up        # Start all services
make migrate   # Run database migrations
make seed      # Load sample data
```

## Tech Stack

- **Languages:** Python, TypeScript, SQL
- **Databases:** PostgreSQL, Neo4j
- **AI:** Claude (Anthropic), OpenAI Embeddings
- **Frameworks:** FastAPI, Next.js, SQLAlchemy
- **Orchestration:** Airflow, Kafka
- **Cloud (AWS):** S3, Glue, Athena, Lambda
- **Infrastructure:** Docker, Terraform, Nginx
- **CI/CD:** GitHub Actions

## Author

**Sean Sullivan**
- GitHub: [sully2490](https://github.com/sully2490)
- LinkedIn: [linkedin.com/in/sean-s-171620171](https://linkedin.com/in/sean-s-171620171)
- Email: shadowandsteel@pm.me
