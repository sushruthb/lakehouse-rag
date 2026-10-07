import json
import uuid
from datetime import date, datetime, timezone

import boto3
import pyarrow as pa
from deltalake import write_deltalake


def _storage_options(endpoint: str, access_key: str, secret_key: str) -> dict:
    return {
        "AWS_ENDPOINT_URL": endpoint,
        "AWS_ACCESS_KEY_ID": access_key,
        "AWS_SECRET_ACCESS_KEY": secret_key,
        "AWS_ALLOW_HTTP": "true",
        "AWS_REGION": "us-east-1",
    }


def write_bronze(
    papers: list[dict],
    minio_endpoint: str,
    access_key: str,
    secret_key: str,
) -> str:
    batch_id = str(uuid.uuid4())
    today = date.today().isoformat()
    s3_key = f"arxiv/{today}/{batch_id}.json"

    s3 = boto3.client(
        "s3",
        endpoint_url=minio_endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    s3.put_object(
        Bucket="bronze",
        Key=s3_key,
        Body=json.dumps(papers).encode("utf-8"),
    )

    table_uri = "s3://bronze/delta/arxiv_raw"
    storage_options = _storage_options(minio_endpoint, access_key, secret_key)
    now = datetime.now(timezone.utc).isoformat()

    schema = pa.schema([
        pa.field("paper_id", pa.string()),
        pa.field("title", pa.string()),
        pa.field("abstract", pa.string()),
        pa.field("authors", pa.list_(pa.string())),
        pa.field("category", pa.string()),
        pa.field("published_date", pa.string()),
        pa.field("batch_id", pa.string()),
        pa.field("ingested_at", pa.string()),
    ])

    data = pa.table(
        {
            "paper_id": [p["paper_id"] for p in papers],
            "title": [p["title"] for p in papers],
            "abstract": [p["abstract"] for p in papers],
            "authors": [p["authors"] for p in papers],
            "category": [p["category"] for p in papers],
            "published_date": [p["published_date"] for p in papers],
            "batch_id": [batch_id] * len(papers),
            "ingested_at": [now] * len(papers),
        },
        schema=schema,
    )

    write_deltalake(
        table_uri,
        data,
        storage_options=storage_options,
        mode="append",
        schema_mode="merge",
        custom_metadata={
            "source": "arxiv",
            "classification": "public",
            "schema_version": "1",
        },
    )

    return f"s3://bronze/{s3_key}"
