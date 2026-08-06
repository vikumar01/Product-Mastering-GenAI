import re
import pandas as pd

BRANDS = ("philips", "samsung", "lg", "acme")
PRODUCT_TYPES = (("bulb", "bulb"), ("lamp", "bulb"), ("television", "tv"), ("tv", "tv"),
                 ("washer", "washing_machine"), ("washing machine", "washing_machine"), ("charger", "charger"))

def normalise(text: str) -> str:
    value = str(text).lower().replace('"', ' inch ')
    value = re.sub(r"\bwatts?\b", "w", value)
    value = re.sub(r"\bkilograms?\b", "kg", value)
    value = re.sub(r"usb[ -]?c", "usb c", value)
    value = re.sub(r"[^a-z0-9.]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def attributes(text: str) -> dict:
    value = normalise(text)
    def number(unit):
        match = re.search(rf"\b(\d+(?:\.\d+)?)\s*{unit}\b", value)
        return float(match.group(1)) if match else None
    return {
        "brand": next((b for b in BRANDS if re.search(rf"\b{b}\b", value)), None),
        "product_type": next((canon for term, canon in PRODUCT_TYPES if term in value), None),
        "watts": number("w"), "capacity_kg": number("kg"), "size_in": number("inch"),
        "colour": next((c for c in ("warm white", "black", "white") if c in value), None),
    }

def prepare(df: pd.DataFrame) -> pd.DataFrame:
    required = {"company", "product_id", "description"}
    if missing := required - set(df.columns):
        raise ValueError(f"Missing columns: {sorted(missing)}")
    result = df.copy()
    result["row_id"] = result["company"].astype(str) + ":" + result["product_id"].astype(str)
    result["normalised_description"] = result["description"].map(normalise)
    extracted = result["description"].map(attributes).apply(pd.Series)
    return pd.concat([result, extracted], axis=1)
