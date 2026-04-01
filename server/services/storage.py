"""Handles all Cloud Storage interactions."""

from google.cloud import storage

from config import settings

_client: storage.Client | None = None


def _get_client() -> storage.Client:
    global _client
    if _client is None:
        _client = storage.Client(project=settings.gcp_project_id)
    return _client


def upload_file(file_bytes: bytes, destination_path: str, content_type: str) -> str:
    """
    Upload raw bytes to GCS and return the gs:// URI.

    Args:
        file_bytes:       Raw file content.
        destination_path: Path inside the bucket, e.g. 'resumes/abc123.pdf'.
        content_type:     MIME type, e.g. 'application/pdf'.

    Returns:
        gs://<bucket>/<destination_path>
    """
    client = _get_client()
    bucket = client.bucket(settings.gcs_bucket_raw)
    blob = bucket.blob(destination_path)

    blob.upload_from_string(file_bytes, content_type=content_type)

    return f"gs://{settings.gcs_bucket_raw}/{destination_path}"
