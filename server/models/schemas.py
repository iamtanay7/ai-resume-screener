from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr


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

class NotifyResponse(BaseModel):
    message: str
