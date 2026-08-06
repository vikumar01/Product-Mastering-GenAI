import pandas as pd

def canonical_products(mapped: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for canonical_id, group in mapped.groupby("canonical_id", sort=True):
        # Prefer the most complete normalised description as a deterministic initial canonical label.
        representative = group.sort_values("normalised_description", key=lambda s: s.str.len(), ascending=False).iloc[0]
        rows.append({"canonical_id": canonical_id, "canonical_description": representative.description,
                     "brand": representative.brand, "product_type": representative.product_type,
                     "member_count": len(group), "source_companies": ",".join(sorted(group.company.unique()))})
    return pd.DataFrame(rows)
