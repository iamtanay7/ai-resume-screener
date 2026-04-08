from datetime import datetime
from typing import Literal

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
    explanation: str
    missingSkills: list[str]
    matchedSkills: list[str]
    rank: int


# ── Notify ────────────────────────────────────────────────────────────────────

class NotifyResponse(BaseModel):
    message: str
