import uuid
from datetime import datetime, timezone

import pyarrow as pa
from deltalake import DeltaTable, write_deltalake


def _storage_options(endpoint: str, access_key: str, secret_key: str) -> dict:
    return {
        "AWS_ENDPOINT_URL": endpoint,
        "AWS_ACCESS_KEY_ID": access_key,
        "AWS_SECRET_ACCESS_KEY": secret_key,
        "AWS_ALLOW_HTTP": "true",
        "AWS_REGION": "us-east-1",
    }


def write_lineage_event(
    source: str,
    target: str,
    model: str,
    minio_endpoint: str,
    access_key: str,
    secret_key: str,
) -> None:
    table_uri = "s3://governance/lineage"
    storage_options = _storage_options(minio_endpoint, access_key, secret_key)
    schema = pa.schema([
        pa.field("event_id", pa.string()),
        pa.field("source", pa.string()),
        pa.field("target", pa.string()),
        pa.field("model", pa.string()),
        pa.field("run_at", pa.string()),
    ])
    data = pa.table(
        {
            "event_id": [str(uuid.uuid4())],
            "source": [source],
            "target": [target],
            "model": [model],
            "run_at": [datetime.now(timezone.utc).isoformat()],
        },
        schema=schema,
    )
    write_deltalake(
        table_uri,
        data,
        storage_options=storage_options,
        mode="append",
        schema_mode="merge",
    )


def get_lineage(
    paper_id: str,
    minio_endpoint: str,
    access_key: str,
    secret_key: str,
) -> list[dict]:
    table_uri = "s3://governance/lineage"
    storage_options = _storage_options(minio_endpoint, access_key, secret_key)
    try:
        dt = DeltaTable(table_uri, storage_options=storage_options)
        df = dt.to_pandas()
        mask = df["source"].str.contains(paper_id) | df["target"].str.contains(paper_id)
        return df[mask].to_dict(orient="records")
    except Exception:
        return []


def log_pipeline_run(
    status: str,
    details: str,
    minio_endpoint: str,
    access_key: str,
    secret_key: str,
) -> None:
    table_uri = "s3://governance/pipeline_runs"
    storage_options = _storage_options(minio_endpoint, access_key, secret_key)
    schema = pa.schema([
        pa.field("run_id", pa.string()),
        pa.field("status", pa.string()),
        pa.field("details", pa.string()),
        pa.field("run_at", pa.string()),
    ])
    data = pa.table(
        {
            "run_id": [str(uuid.uuid4())],
            "status": [status],
            "details": [details],
            "run_at": [datetime.now(timezone.utc).isoformat()],
        },
        schema=schema,
    )
    write_deltalake(
        table_uri,
        data,
        storage_options=storage_options,
        mode="append",
        schema_mode="merge",
    )
