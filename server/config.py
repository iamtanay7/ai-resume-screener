from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    gcp_project_id: str = "your-project-id"
    gcs_bucket_raw: str = "resume-screener-raw"
    pubsub_topic_resume: str = "resume-uploaded"
    pubsub_topic_jd: str = "jd-uploaded"
    max_file_size_bytes: int = 10 * 1024 * 1024  # 10 MB
    cors_origin: str = "http://localhost:3000"


settings = Settings()
