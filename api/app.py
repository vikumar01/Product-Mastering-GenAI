from fastapi import FastAPI
from src.pipeline import run

app = FastAPI(title="Product Mastering API")

@app.post("/run")
def run_mastering():
    mapped, canonicals, pairs = run()
    return {"source_products": len(mapped), "canonical_products": len(canonicals), "review_pairs": int((pairs.decision == "review").sum())}
