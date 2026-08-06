import json
import os
import boto3

sf = boto3.client("stepfunctions")

def lambda_handler(event, _context):
    """Start one workflow execution per uploaded CSV."""
    for record in event["Records"]:
        sf.start_execution(
            stateMachineArn=os.environ["STATE_MACHINE_ARN"],
            input=json.dumps({"bucket": record["s3"]["bucket"]["name"], "key": record["s3"]["object"]["key"]}),
        )
    return {"started": len(event["Records"])}
