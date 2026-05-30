# Database Workspace

This area covers the offline intelligence pipeline and persistence layer for TransitionAI Zurich.

## Suggested ownership

- Eduardo: CV extraction outputs and normalized profile schemas
- Shai: embeddings, vector storage, knowledge graph, and relationship modeling
- Shared: ingestion contracts, normalized skills, migrations, and seeds

## Structure

- `ingestion/`: adapters for Zurich job APIs and labor-market data sources
- `normalized/`: structured intermediate outputs such as jobs, skills, and trend entities
- `embeddings/`: embedding generation jobs and vector-ready artifacts
- `knowledge_graph/`: graph schemas, edge builders, and traversal helpers
- `migrations/`: database schema migrations
- `seeds/`: demo fixtures and local bootstrap datasets
- `schemas/`: shared data contracts for jobs, skills, profiles, and transitions
