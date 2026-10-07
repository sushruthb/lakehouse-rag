from unittest.mock import patch, MagicMock
import pytest
from bronze_writer import write_bronze


SAMPLE_PAPERS = [
    {
        "paper_id": "2301.00001",
        "title": "Test Paper",
        "abstract": "Abstract text.",
        "authors": ["Author One"],
        "category": "cs.AI",
        "published_date": "2023-01-01",
    }
]


def test_write_bronze_returns_s3_path():
    with patch("bronze_writer.boto3.client") as mock_boto, \
         patch("bronze_writer.write_deltalake") as mock_delta:
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        path = write_bronze(
            SAMPLE_PAPERS,
            minio_endpoint="http://localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
        )

    assert path.startswith("s3://bronze/arxiv/")
    assert mock_s3.put_object.called
    assert mock_delta.called
