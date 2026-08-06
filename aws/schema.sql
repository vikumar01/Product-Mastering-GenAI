CREATE TABLE IF NOT EXISTS canonical_product (
  canonical_id UUID PRIMARY KEY, canonical_description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS product_mapping (
  source_row_id TEXT PRIMARY KEY, company TEXT NOT NULL, product_id TEXT NOT NULL,
  canonical_id UUID NOT NULL, decision TEXT NOT NULL, hybrid_score NUMERIC(5,4),
  decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
