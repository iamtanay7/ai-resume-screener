from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    gcp_project_id: str = "your-project-id"
    gcs_bucket_raw: str = "resume-screener-raw"
    pubsub_topic_resume: str = "resume-uploaded"
    pubsub_topic_jd: str = "jd-uploaded"
    max_file_size_bytes: int = 10 * 1024 * 1024  # 10 MB
    cors_origin: str = "http://localhost:3000"

    ranking_weight_skills: float = 0.4
    ranking_weight_experience: float = 0.3
    ranking_weight_education: float = 0.15
    ranking_weight_keywords: float = 0.15
    ranking_threshold_shortlist: float = 75.0
    ranking_threshold_manual_review: float = 55.0
    ranking_version: str = "v1"


settings = Settings()
