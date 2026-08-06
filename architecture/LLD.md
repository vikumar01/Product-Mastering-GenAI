# Low-Level Design

1. `preprocess.prepare` validates required columns, creates a stable `company:product_id` source key, normalises text and extracts attributes.
2. `Embedder` generates normalised SentenceTransformer vectors. Its TF-IDF fallback is a demonstration resilience feature, not the recommended production semantic model.
3. `score_pairs` compares cross-company candidates and computes `0.60 semantic + 0.15 lexical + 0.25 attributes`. Any incompatible populated attribute makes the result `separate`.
4. `clusters` uses connected components only over `auto_merge` edges. Review edges are deliberately excluded, preventing transitive over-merges.
5. `canonical_mapper` assigns stable run-local IDs and selects a representative description. Production should use a curated label or an LLM-generated label with approval.

## Acceptance and monitoring

Create a labelled pair set stratified by category and supplier. Report precision, recall, F1, false-merge rate, review rate and cluster purity each model/rule release. A false merge is generally costlier than a missed merge, so tune thresholds to a precision target before increasing automation.
