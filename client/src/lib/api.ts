import type {
  ProcessingStatusResponse,
  Candidate,
  ExplainabilityRankingData,
  ExplainabilityResponse,
  JobDescription,
  UploadJDResponse,
  UploadResumeResponse,
} from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (process.env.NODE_ENV === "development"
    ? "http://localhost:8000"
    : "https://resume-api-253408457990.us-central1.run.app");

export function getDocumentPreviewUrl(gcsUri: string): string {
  const url = new URL(`${BASE_URL}/upload/file`);
  url.searchParams.set("gcsUri", gcsUri);
  return url.toString();
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(
      (body as { message?: string }).message ?? `HTTP ${res.status}`
    );
  }
  return res.json() as Promise<T>;
}

export async function uploadJD(
  file: File,
  jobTitle: string
): Promise<UploadJDResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("jobTitle", jobTitle);

  const res = await fetch(`${BASE_URL}/upload/jd`, {
    method: "POST",
    body: form,
  });
  return handleResponse<UploadJDResponse>(res);
}

export async function uploadResume(
  file: File,
  email: string,
  name: string,
  jobId: string
): Promise<UploadResumeResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("email", email);
  form.append("name", name);
  form.append("jobId", jobId);

  const res = await fetch(`${BASE_URL}/upload/resume`, {
    method: "POST",
    body: form,
  });
  return handleResponse<UploadResumeResponse>(res);
}

export async function getResults(jobId: string): Promise<Candidate[]> {
  const res = await fetch(`${BASE_URL}/results/${jobId}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  return handleResponse<Candidate[]>(res);
}

export async function approveEmail(candidateId: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/notify/${candidateId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  return handleResponse<void>(res);
}

export async function getResumeStatus(
  candidateId: string
): Promise<ProcessingStatusResponse> {
  const res = await fetch(`${BASE_URL}/upload/resume/${candidateId}/status`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  return handleResponse<ProcessingStatusResponse>(res);
}

export async function getJDStatus(
  jobId: string
): Promise<ProcessingStatusResponse> {
  const res = await fetch(`${BASE_URL}/upload/jd/${jobId}/status`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  return handleResponse<ProcessingStatusResponse>(res);
}

export async function getUploadedJDs(): Promise<JobDescription[]> {
  const res = await fetch(`${BASE_URL}/upload/jds`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  return handleResponse<JobDescription[]>(res);
}

export async function generateExplanation(
  candidateId: string
): Promise<ExplainabilityResponse> {
  const res = await fetch(`${BASE_URL}/explainability/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      mode: "candidate_id",
      candidate_id: candidateId,
    }),
  });
  return handleResponse<ExplainabilityResponse>(res);
}

export async function generateExplanationFromRanking(
  rankingData: ExplainabilityRankingData
): Promise<ExplainabilityResponse> {
  const res = await fetch(`${BASE_URL}/explainability/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      mode: "ranking_data",
      candidate_id: rankingData.candidate_id,
      ranking_data: rankingData,
    }),
  });
  return handleResponse<ExplainabilityResponse>(res);
}
