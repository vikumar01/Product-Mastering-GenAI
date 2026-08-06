import csv
import io
import json
import os
import re
import uuid
from datetime import datetime, timezone

import boto3
from opensearchpy import AWSV4SignerAuth, OpenSearch, RequestsHttpConnection

s3 = boto3.client("s3")
bedrock = boto3.client("bedrock-runtime")
rds = boto3.client("rds-data")
BRANDS = ("philips", "samsung", "lg", "acme")
TYPES = (("washing machine", "washing_machine"), ("washer", "washing_machine"), ("television", "tv"), ("tv", "tv"), ("bulb", "bulb"), ("lamp", "bulb"), ("charger", "charger"))
ATTRIBUTES = ("brand", "product_type", "watts", "capacity_kg", "size_in", "colour")

def normalise(text):
    value = str(text).lower().replace('"', ' inch ')
    value = re.sub(r"\bwatts?\b", "w", value)
    value = re.sub(r"\bkilograms?\b", "kg", value)
    value = re.sub(r"usb[ -]?c", "usb c", value)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9.]+", " ", value)).strip()

def extract(text):
    value = normalise(text)
    def number(unit):
        matched = re.search(rf"\b(\d+(?:\.\d+)?)\s*{unit}\b", value)
        return float(matched.group(1)) if matched else None
    return {"brand": next((x for x in BRANDS if re.search(rf"\b{x}\b", value)), None),
            "product_type": next((kind for term, kind in TYPES if term in value), None),
            "watts": number("w"), "capacity_kg": number("kg"), "size_in": number("inch"),
            "colour": next((x for x in ("warm white", "black", "white") if x in value), None)}

def create_embedding(text):
    response = bedrock.invoke_model(modelId=os.environ["EMBEDDING_MODEL_ID"], contentType="application/json", accept="application/json", body=json.dumps({"inputText": text, "dimensions": 1024, "normalize": True}))
    return json.loads(response["body"].read())["embedding"]

def search_client():
    host = os.environ["OPENSEARCH_ENDPOINT"].replace("https://", "").rstrip("/")
    auth = AWSV4SignerAuth(boto3.Session().get_credentials(), os.environ["AWS_REGION"], "aoss")
    return OpenSearch(hosts=[{"host": host, "port": 443}], http_auth=auth, use_ssl=True, verify_certs=True, connection_class=RequestsHttpConnection)

def compare(product, candidate):
    semantic = max(0, min(1, sum(x * y for x, y in zip(product["embedding"], candidate["embedding"]))))
    a, b = set(product["normalised_description"].split()), set(candidate["normalised_description"].split())
    lexical = len(a & b) / max(1, len(a | b))
    matches = comparable = 0
    for name in ATTRIBUTES:
        left, right = product.get(name), candidate.get(name)
        if left is None or right is None: continue
        comparable += 1
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            if abs(left - right) > .01: return {"hybrid_score": 0, "attribute_conflict": True}
        elif left != right: return {"hybrid_score": 0, "attribute_conflict": True}
        matches += 1
    attribute = matches / comparable if comparable else .5
    return {"semantic_score": round(semantic, 4), "lexical_score": round(lexical, 4), "attribute_score": round(attribute, 4), "hybrid_score": round(.60 * semantic + .15 * lexical + .25 * attribute, 4), "attribute_conflict": False}

def validate_with_claude(product, candidate):
    prompt = """Are these the same sellable product? Different wattage, capacity, dimensions, pack size, model number, or incompatible brand means false. Return JSON only with same_product (boolean), confidence (0 to 1), reason, and canonical_description when true.\nA=""" + json.dumps({x: product.get(x) for x in ("description", *ATTRIBUTES)}) + "\nB=" + json.dumps({x: candidate.get(x) for x in ("description", *ATTRIBUTES)})
    response = bedrock.converse(modelId=os.environ["CLAUDE_MODEL_ID"], system=[{"text": "Return valid JSON only; do not guess."}], messages=[{"role": "user", "content": [{"text": prompt}]}], inferenceConfig={"temperature": 0, "maxTokens": 300})
    text = response["output"]["message"]["content"][0]["text"].strip().removeprefix("```json").removesuffix("```").strip()
    return json.loads(text)

def persist(product, canonical_id, decision, scores):
    if not os.environ.get("DB_CLUSTER_ARN"): return
    values = [("source_row_id", product["source_row_id"]), ("company", product["company"]), ("product_id", product["product_id"]), ("canonical_id", canonical_id), ("decision", decision)]
    parameters = [{"name": key, "value": {"stringValue": value}} for key, value in values] + [{"name": "score", "value": {"doubleValue": scores["hybrid_score"]}}]
    rds.execute_statement(resourceArn=os.environ["DB_CLUSTER_ARN"], secretArn=os.environ["DB_SECRET_ARN"], database=os.environ["DB_NAME"], parameters=parameters, sql="""INSERT INTO product_mapping(source_row_id,company,product_id,canonical_id,decision,hybrid_score) VALUES(:source_row_id,:company,:product_id,CAST(:canonical_id AS uuid),:decision,:score) ON CONFLICT (source_row_id) DO UPDATE SET canonical_id=EXCLUDED.canonical_id, decision=EXCLUDED.decision, hybrid_score=EXCLUDED.hybrid_score, decided_at=now()""")

def resolve(row, search):
    product = {"source_row_id": f"{row['company']}:{row['product_id']}", "company": row["company"], "product_id": row["product_id"], "description": row["description"], "normalised_description": normalise(row["description"]), **extract(row["description"])}
    product["embedding"] = create_embedding(product["normalised_description"])
    response = search.search(index=os.environ["OPENSEARCH_INDEX"], body={"size": 25, "query": {"knn": {"embedding": {"vector": product["embedding"], "k": 25}}}})
    candidates = [x["_source"] for x in response["hits"]["hits"] if x["_source"]["company"] != product["company"]]
    scores, best = max(((compare(product, item), item) for item in candidates), key=lambda x: x[0]["hybrid_score"], default=({"hybrid_score": 0, "attribute_conflict": False}, None))
    decision, claude = "separate", None
    canonical_id = str(uuid.uuid5(uuid.NAMESPACE_URL, product["source_row_id"]))
    if best and not scores["attribute_conflict"] and scores["hybrid_score"] >= .92:
        decision, canonical_id = "auto_merge", best["canonical_id"]
    elif best and not scores["attribute_conflict"] and scores["hybrid_score"] >= .82:
        try:
            claude = validate_with_claude(product, best)
            if claude.get("same_product") and float(claude.get("confidence", 0)) >= .95: decision, canonical_id = "claude_merge", best["canonical_id"]
            else: decision = "review"
        except (ValueError, json.JSONDecodeError):
            decision = "review"
    product["canonical_id"] = canonical_id
    # A refresh makes earlier rows in this file available as candidates for later rows.
    # Replace this with bulk indexing / batch stages for high-volume backfills.
    search.index(index=os.environ["OPENSEARCH_INDEX"], id=product["source_row_id"], body=product, refresh="wait_for")
    persist(product, canonical_id, decision, scores)
    return {"source_row_id": product["source_row_id"], "canonical_id": canonical_id, "decision": decision, "scores": scores, "matched_source_row_id": best and best["source_row_id"], "claude": claude}

def lambda_handler(event, _context):
    body = s3.get_object(Bucket=event["bucket"], Key=event["key"])["Body"].read().decode("utf-8-sig")
    search = search_client()
    results = [resolve(row, search) for row in csv.DictReader(io.StringIO(body))]
    key = f"runs/{datetime.now(timezone.utc):%Y-%m-%dT%H-%M-%SZ}/resolution.json"
    s3.put_object(Bucket=os.environ["AUDIT_BUCKET"], Key=key, Body=json.dumps(results), ContentType="application/json")
    return {"processed": len(results), "audit_s3_key": key, "review_count": sum(x["decision"] == "review" for x in results)}
