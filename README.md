# Product Mastering with GenAI

This project consolidates equivalent products supplied by different organisations into auditable canonical products. It uses a **hybrid score**: semantic embeddings understand meaning, lexical matching protects against wording changes, and extracted attributes prevent unsafe matches such as a 50W bulb being merged with a 9W bulb.

## Quick start

```powershell
cd C:\Users\vivek\Documents\Codex\2026-07-30\files-mentioned-by-the-user-claim\outputs\Product-Mastering-GenAI
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.pipeline
```

The first run downloads `all-MiniLM-L6-v2`. If it is unavailable, the pipeline automatically uses TF-IDF so the supplied demonstration still runs. Results are written to `outputs/`.

## Decision policy

| Hybrid score | Action | Rationale |
|---:|---|---|
| >= 0.92 | auto_merge | Strong semantic, lexical and attribute agreement |
| 0.82–0.92 | review | A reviewer or LLM must confirm the proposed pair |
| < 0.82 | separate | Do not join products |

Hard conflicts in extracted numeric attributes (for example, 50W vs 9W) block a merge even when description similarity is high.

## Production deployment

Use PostgreSQL + pgvector or Chroma/HNSW for approximate nearest-neighbour candidate generation. Retain the final hybrid decision, model/version, attributes, reviewer decision and timestamps. Only compare a new product with candidate neighbours rather than rebuilding all pair scores. Treat an LLM as a validator for ambiguous candidates, never as the only matching control.

Run an API locally with `uvicorn api.app:app --reload`. The core pipeline is intentionally storage-agnostic; replace CSV ingestion/export with database repositories in production.

## Output contracts

| File | Grain | Purpose |
|---|---|---|
| `similarity_scores.csv` | candidate pair | scores, extracted attributes and routing decision |
| `product_clusters.csv` | source product | original-to-canonical mapping |
| `canonical_products.csv` | canonical product | cluster representative and member count |
| `review_queue.csv` | uncertain pair | proposed matches requiring validation |
