from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


# ── Upload responses ──────────────────────────────────────────────────────────

class UploadResumeResponse(BaseModel):
    candidateId: str
    message: str


class UploadJDResponse(BaseModel):
    jobId: str
    message: str


# ── Firestore document shapes ─────────────────────────────────────────────────

class CandidateRecord(BaseModel):
    id: str
    name: str
    email: EmailStr
    resumeUrl: str          # gs:// path
    uploadedAt: datetime
    status: str = "uploaded"


class JobRecord(BaseModel):
    id: str
    title: str
    fileUrl: str            # gs:// path
    uploadedAt: datetime
    status: str = "uploaded"


# ── NLP processing (Tanay) ────────────────────────────────────────────────────

DocumentKind = Literal["resume", "job_description"]
PipelineStage = Literal["uploaded", "parsing", "parsed", "embedding", "processed", "failed"]


class DocumentSection(BaseModel):
    title: str
    content: str


class ParsedDocument(BaseModel):
    documentId: str
    kind: DocumentKind
    sourceUrl: str
    extractedText: str
    sections: list[DocumentSection]
    metadata: dict[str, str] = Field(default_factory=dict)


class EmbeddingRecord(BaseModel):
    model: str
    vector: list[float]
    textSnippet: str


# ── Pub/Sub ingestion ─────────────────────────────────────────────────────────

class PubSubMessage(BaseModel):
    data: str
    messageId: str | None = None
    publishTime: str | None = None
    attributes: dict[str, str] = Field(default_factory=dict)


class PubSubPushEnvelope(BaseModel):
    message: PubSubMessage
    subscription: str | None = None


class IngestionResponse(BaseModel):
    message: str
    documentId: str
    eventType: str


# ── Processing status ─────────────────────────────────────────────────────────

class ProcessingStatusResponse(BaseModel):
    documentId: str
    status: PipelineStage
    processingError: str | None = None


class JobListItem(BaseModel):
    id: str
    title: str
    fileUrl: str
    uploadedAt: datetime | str
    status: str
    processingError: str | None = None


# ── Results (written by Michael's ranking engine, read here) ──────────────────

CandidateStatus = Literal["shortlist", "manual_review", "reject"]


class ScoreBreakdown(BaseModel):
    skills: float
    experience: float
    education: float
    keywords: float
    overall: float


class RankedCandidate(BaseModel):
    id: str
    name: str
    email: str
    resumeUrl: str
    scoreBreakdown: ScoreBreakdown
    status: CandidateStatus
    explanation: str | None = None
    missingSkills: list[str]
    matchedSkills: list[str]
    rank: int


class RankingTriggerRequest(BaseModel):
    """Trigger payload emitted after Tanay's processing stage completes."""

    jobId: str
    candidateIds: list[str] | None = None


class RankingTriggerResponse(BaseModel):
    message: str
    jobId: str


# ── Notify ────────────────────────────────────────────────────────────────────

class RankingDataPayload(BaseModel):
    candidate_name: str
    overall_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    candidate_id: str | None = None
    job_title: str | None = None
    score_breakdown: dict[str, int] | None = None
    years_experience: int | None = None
    jd_summary: str | None = None

    model_config = {"extra": "allow"}


class ExplainabilityRequest(BaseModel):
    mode: Literal["candidate_id", "ranking_data"] = "candidate_id"
    candidate_id: str | None = None
    ranking_data: RankingDataPayload | dict[str, Any] | None = None


class ExplainabilityResponse(BaseModel):
    candidate_id: str
    candidate_name: str
    job_title: str
    overall_score: int
    years_experience: int
    decision: Literal["shortlist", "manual_review", "reject"]
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    recommendation: str
    score_breakdown: dict[str, int]
    matched_skills: list[str]
    missing_skills: list[str]
    confidence_score: int
    jd_summary: str
    fairness_note: str
    source: str


class NotifyResponse(BaseModel):
    message: str
