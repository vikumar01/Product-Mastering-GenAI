from pathlib import Path
import pandas as pd
from .config import SETTINGS
from .preprocess import prepare
from .embedding_generator import Embedder
from .similarity_engine import score_pairs
from .clustering import clusters
from .canonical_mapper import canonical_products

def run(data_dir: Path = SETTINGS.data_dir, output_dir: Path = SETTINGS.output_dir):
    source_files = sorted(data_dir.glob("company*_products.csv"))
    if not source_files: raise FileNotFoundError(f"No company CSV files found in {data_dir}")
    products = prepare(pd.concat([pd.read_csv(f) for f in source_files], ignore_index=True))
    embedder = Embedder(SETTINGS.embedding_model)
    pairs = score_pairs(products, embedder.fit_transform(products.normalised_description), SETTINGS)
    mapped = clusters(products, pairs)
    canonicals = canonical_products(mapped)
    output_dir.mkdir(parents=True, exist_ok=True)
    pairs.to_csv(output_dir / "similarity_scores.csv", index=False)
    pairs[pairs.decision == "review"].to_csv(output_dir / "review_queue.csv", index=False)
    mapped.to_csv(output_dir / "product_clusters.csv", index=False)
    canonicals.to_csv(output_dir / "canonical_products.csv", index=False)
    print(f"Embedding backend: {embedder.backend}; {len(products)} source products -> {len(canonicals)} canonical products")
    return mapped, canonicals, pairs

if __name__ == "__main__": run()
