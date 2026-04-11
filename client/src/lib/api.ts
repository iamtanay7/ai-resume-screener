import type {
  ProcessingStatusResponse,
  Candidate,
  UploadJDResponse,
  UploadResumeResponse,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
  name: string
): Promise<UploadResumeResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("email", email);
  form.append("name", name);

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
