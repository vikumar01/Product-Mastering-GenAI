# Deploy the AWS implementation

## One-time console setup

1. Select a target Region. In Bedrock **Model catalog**, complete the Anthropic first-time-use form and copy the current Claude inference-profile/model ID. Ensure Titan Text Embeddings V2 is available.
2. Create an OpenSearch Serverless collection of type **Vector search**. Configure its encryption, network and data-access policies to permit the resolver Lambda role. Create index `products-v1` from `opensearch_index.json`; its vector dimension is 1024.
3. Optional: create Aurora PostgreSQL Serverless v2, enable the RDS Data API, save credentials in Secrets Manager and run `schema.sql`. Leave database parameters blank for an S3-only trial.

## Build and deploy

```powershell
cd C:\Users\vivek\Documents\Codex\2026-07-30\files-mentioned-by-the-user-claim\outputs\Product-Mastering-GenAI\aws
sam build
sam deploy --guided
```

Supply the OpenSearch HTTPS collection endpoint, `products-v1`, a valid current Claude ID and optional Aurora values. The initial policy intentionally uses broad resources so the first deployment can succeed; replace these with explicit model, collection, database and secret ARNs before production.

## Run

Upload a CSV with `company,product_id,description` headers to the CloudFormation `RawBucketName` output. S3 invokes `StartWorkflowFunction`, which starts Step Functions and runs the resolver. Result and review decisions are saved in the `AuditBucketName` output under `runs/`.

For large historical loads, split source files and use a Step Functions Map state with Bedrock retry/backoff and batch embedding. Keep `review` records for human validation; never treat low-confidence Claude output as an auto-merge.
