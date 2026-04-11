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

    ranking_weight_skills: float = 0.4
    ranking_weight_experience: float = 0.3
    ranking_weight_education: float = 0.15
    ranking_weight_keywords: float = 0.15
    ranking_threshold_shortlist: float = 75.0
    ranking_threshold_manual_review: float = 55.0
    ranking_version: str = "v1"

    def model_post_init(self, __context):
        """Validate that ranking weights sum to 1.0 within tolerance."""
        weights_sum = (
            self.ranking_weight_skills
            + self.ranking_weight_experience
            + self.ranking_weight_education
            + self.ranking_weight_keywords
        )
        epsilon = 1e-6
        if abs(weights_sum - 1.0) > epsilon:
            raise ValueError(
                f"Ranking weights must sum to 1.0, got {weights_sum}. "
                f"Current: skills={self.ranking_weight_skills}, "
                f"experience={self.ranking_weight_experience}, "
                f"education={self.ranking_weight_education}, "
                f"keywords={self.ranking_weight_keywords}"
            )


settings = Settings()
