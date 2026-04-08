from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    gcp_project_id: str = "your-project-id"
    gcp_region: str = "us-central1"
    gcs_bucket_raw: str = "resume-screener-raw"
    pubsub_topic_resume: str = "resume-uploaded"
    pubsub_topic_jd: str = "jd-uploaded"
    document_ai_location: str = "us"
    document_ai_resume_processor_id: str = "resume-processor-id"
    document_ai_jd_processor_id: str = "jd-processor-id"
    vertex_embedding_model: str = "text-embedding-005"
    max_file_size_bytes: int = 10 * 1024 * 1024  # 10 MB
    cors_origin: str = "http://localhost:3000"


settings = Settings()
