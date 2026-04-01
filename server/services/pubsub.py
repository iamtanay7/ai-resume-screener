"""Handles all Pub/Sub interactions."""

import json
import logging

from google.cloud import pubsub_v1

from config import settings

logger = logging.getLogger(__name__)

_publisher: pubsub_v1.PublisherClient | None = None


def _get_publisher() -> pubsub_v1.PublisherClient:
    global _publisher
    if _publisher is None:
        _publisher = pubsub_v1.PublisherClient()
    return _publisher


def _topic_path(topic_name: str) -> str:
    return f"projects/{settings.gcp_project_id}/topics/{topic_name}"


def publish_resume_uploaded(candidate_id: str, gcs_path: str, email: str) -> None:
    """
    Notify downstream pipeline that a resume is ready for processing.
    Tanay's ingestion service subscribes to this topic.
    """
    payload = {
        "type": "resume_uploaded",
        "candidateId": candidate_id,
        "gcsPath": gcs_path,
        "email": email,
    }
    _publish(settings.pubsub_topic_resume, payload)
    logger.info("Published resume_uploaded for candidate %s", candidate_id)


def publish_jd_uploaded(job_id: str, gcs_path: str, title: str) -> None:
    """
    Notify downstream pipeline that a JD is ready for processing.
    """
    payload = {
        "type": "jd_uploaded",
        "jobId": job_id,
        "gcsPath": gcs_path,
        "title": title,
    }
    _publish(settings.pubsub_topic_jd, payload)
    logger.info("Published jd_uploaded for job %s", job_id)


def _publish(topic_name: str, payload: dict) -> None:
    publisher = _get_publisher()
    topic = _topic_path(topic_name)
    data = json.dumps(payload).encode("utf-8")
    future = publisher.publish(topic, data)
    future.result()  # block until confirmed
