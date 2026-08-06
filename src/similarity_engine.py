import json
import numpy as np
import pandas as pd
from .config import Settings

ATTRIBUTE_COLUMNS = ("brand", "product_type", "watts", "capacity_kg", "size_in", "colour")

def _lexical(a, b):
    left, right = set(a.split()), set(b.split())
    return len(left & right) / max(len(left | right), 1)

def _attribute_score(left, right):
    agreements, comparable = 0, 0
    for col in ATTRIBUTE_COLUMNS:
        a, b = left[col], right[col]
        if pd.isna(a) or pd.isna(b):
            continue
        comparable += 1
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if abs(float(a) - float(b)) > 0.01:
                return 0.0, True
            agreements += 1
        elif a == b:
            agreements += 1
        else:
            return 0.0, True
    return (agreements / comparable if comparable else 0.5), False

def score_pairs(products, vectors, settings: Settings):
    rows = []
    for i in range(len(products)):
        for j in range(i + 1, len(products)):
            a, b = products.iloc[i], products.iloc[j]
            if a.company == b.company:  # source IDs within one supplier need separate governance
                continue
            semantic = float(np.clip(np.dot(vectors[i], vectors[j]), 0, 1))
            lexical = _lexical(a.normalised_description, b.normalised_description)
            attr, conflict = _attribute_score(a, b)
            hybrid = 0.0 if conflict else (settings.semantic_weight * semantic + settings.lexical_weight * lexical + settings.attribute_weight * attr)
            decision = "separate" if conflict or hybrid < settings.review_threshold else ("auto_merge" if hybrid >= settings.auto_merge_threshold else "review")
            rows.append({"left_row_id": a.row_id, "right_row_id": b.row_id, "semantic_score": round(semantic, 4),
                         "lexical_score": round(lexical, 4), "attribute_score": round(attr, 4), "attribute_conflict": conflict,
                         "hybrid_score": round(hybrid, 4), "decision": decision,
                         "left_attributes": json.dumps({c: a[c] for c in ATTRIBUTE_COLUMNS}, default=str),
                         "right_attributes": json.dumps({c: b[c] for c in ATTRIBUTE_COLUMNS}, default=str)})
    return pd.DataFrame(rows)
