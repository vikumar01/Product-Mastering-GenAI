# High-Level Design

## Flow

`Source CSV/database -> standardise + extract attributes -> embeddings -> candidate retrieval -> hybrid score -> auto merge / review / reject -> canonical master + audit exports`

| Component | Responsibility | Production choice |
|---|---|---|
| Ingestion | Validate supplier feed and assign immutable source row IDs | Airflow/DBT + PostgreSQL |
| Understanding | Normalise units and extract brand/type/specifications | Rules plus constrained LLM extraction |
| Retrieval | Find plausible cross-company neighbours | pgvector HNSW or Chroma |
| Resolution | Apply hard attribute rules and hybrid decision policy | Python service |
| Review | Confirm medium-confidence pairs | UI with accept/reject and reason |
| Master data | Persist canonical product and original mappings | PostgreSQL |

## Data model

| Table | Key fields |
|---|---|
| `source_product` | source_row_id, company_id, product_id, raw_description, normalised_description, embedding, model_version |
| `canonical_product` | canonical_id, canonical_description, product_type, brand, active_version |
| `product_mapping` | source_row_id, canonical_id, decision, score, reviewer, decided_at |
| `match_audit` | pair IDs, individual scores, attributes, rule outcome, prompt/model version |

Candidate retrieval must be restricted by language/category where available. Exact constraints (wattage, voltage, capacity, pack count, dimensions) are merge blockers unless an approved unit-conversion rule proves equivalence.
