import type {
  AuthTokenResponse,
  ProcessingStatusResponse,
  Candidate,
  ExplainabilityRankingData,
  ExplainabilityResponse,
  JobDescription,
  UploadJDResponse,
  UploadResumeResponse,
  UserRole,
} from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (process.env.NODE_ENV === "development"
    ? "http://localhost:8000"
    : "https://resume-api-253408457990.us-central1.run.app");

const TOKEN_KEY = "resumeai:token";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

function authHeaders(): HeadersInit {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function getDocumentPreviewUrl(gcsUri: string): string {
  const token = getStoredToken();
  const url = new URL(`${BASE_URL}/upload/file`);
  url.searchParams.set("gcsUri", gcsUri);
  if (token) url.searchParams.set("token", token);
  return url.toString();
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(
      (body as { detail?: string; message?: string }).detail ??
        (body as { message?: string }).message ??
        `HTTP ${res.status}`
    );
  }
  return res.json() as Promise<T>;
}

export async function signup(
  name: string,
  email: string,
  password: string,
  role: UserRole
): Promise<AuthTokenResponse> {
  const res = await fetch(`${BASE_URL}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password, role }),
  });
  return handleResponse<AuthTokenResponse>(res);
}

export async function login(
  email: string,
  password: string
): Promise<AuthTokenResponse> {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return handleResponse<AuthTokenResponse>(res);
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
    headers: authHeaders(),
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
    headers: authHeaders(),
    body: form,
  });
  return handleResponse<UploadResumeResponse>(res);
}

export async function getResults(jobId: string): Promise<Candidate[]> {
  const res = await fetch(`${BASE_URL}/results/${jobId}`, {
    method: "GET",
    headers: { "Content-Type": "application/json", ...authHeaders() },
  });
  return handleResponse<Candidate[]>(res);
}

export async function approveEmail(candidateId: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/notify/${candidateId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
  });
  return handleResponse<void>(res);
}

export async function getResumeStatus(
  candidateId: string
): Promise<ProcessingStatusResponse> {
  const res = await fetch(`${BASE_URL}/upload/resume/${candidateId}/status`, {
    method: "GET",
    headers: { "Content-Type": "application/json", ...authHeaders() },
  });
  return handleResponse<ProcessingStatusResponse>(res);
}

export async function getJDStatus(
  jobId: string
): Promise<ProcessingStatusResponse> {
  const res = await fetch(`${BASE_URL}/upload/jd/${jobId}/status`, {
    method: "GET",
    headers: { "Content-Type": "application/json", ...authHeaders() },
  });
  return handleResponse<ProcessingStatusResponse>(res);
}

export async function getUploadedJDs(): Promise<JobDescription[]> {
  const res = await fetch(`${BASE_URL}/upload/jds`, {
    method: "GET",
    headers: { "Content-Type": "application/json", ...authHeaders() },
  });
  return handleResponse<JobDescription[]>(res);
}

export async function generateExplanation(
  candidateId: string
): Promise<ExplainabilityResponse> {
  const res = await fetch(`${BASE_URL}/explainability/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
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
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({
      mode: "ranking_data",
      candidate_id: rankingData.candidate_id,
      ranking_data: rankingData,
    }),
  });
  return handleResponse<ExplainabilityResponse>(res);
}
