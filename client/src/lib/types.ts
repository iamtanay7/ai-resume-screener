export type CandidateStatus = "shortlist" | "manual_review" | "reject";

export type PipelineStageStatus = "pending" | "processing" | "done" | "error";
export type BackendProcessingStatus =
  | "uploaded"
  | "parsing"
  | "parsed"
  | "embedding"
  | "processed"
  | "failed";

export interface ScoreBreakdown {
  skills: number;      // 0–100, weight 40%
  experience: number;  // 0–100, weight 30%
  education: number;   // 0–100, weight 15%
  keywords: number;    // 0–100, weight 15%
  overall: number;     // weighted composite
}

export interface Candidate {
  id: string;
  name: string;
  email: string;
  resumeUrl: string;
  scoreBreakdown: ScoreBreakdown;
  status: CandidateStatus;
  explanation: string;
  missingSkills: string[];
  matchedSkills: string[];
  rank: number;
}

export interface JobDescription {
  id: string;
  title: string;
  fileUrl: string;
  uploadedAt: string;
}

export interface PipelineStage {
  label: string;
  status: PipelineStageStatus;
}

export interface UploadResumeResponse {
  candidateId: string;
  message: string;
}

export interface UploadJDResponse {
  jobId: string;
  message: string;
}

export interface ProcessingStatusResponse {
  documentId: string;
  status: BackendProcessingStatus;
  processingError: string | null;
}

export interface ApiError {
  message: string;
  code?: string;
}

export interface ExplainabilityResponse {
  candidate_id: string;
  candidate_name: string;
  job_title: string;
  overall_score: number;
  years_experience: number;
  decision: CandidateStatus;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  recommendation: string;
  score_breakdown: Record<string, number>;
  matched_skills: string[];
  missing_skills: string[];
  confidence_score: number;
  jd_summary: string;
  fairness_note: string;
  source: string;
}

export interface ExplainabilityRankingData {
  candidate_id: string;
  candidate_name: string;
  job_title?: string;
  overall_score: number;
  matched_skills: string[];
  missing_skills: string[];
  score_breakdown?: Record<string, number>;
  years_experience?: number;
  jd_summary?: string;
}
