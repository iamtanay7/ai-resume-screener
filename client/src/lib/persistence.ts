export interface CandidateUploadState {
  candidateId: string;
  name: string;
  email: string;
  jobId: string;
}

export interface RecruiterUploadState {
  jobId: string;
  jobTitle: string;
}

export interface RecruiterJobHistoryItem {
  jobId: string;
  jobTitle: string;
}

export const CANDIDATE_UPLOAD_STORAGE_KEY = "resumeai:candidate-upload";
export const RECRUITER_UPLOAD_STORAGE_KEY = "resumeai:recruiter-upload";
export const RECRUITER_JOB_HISTORY_STORAGE_KEY = "resumeai:recruiter-jobs";

function readJson<T>(key: string): T | null {
  if (typeof window === "undefined") return null;

  const raw = window.localStorage.getItem(key);
  if (!raw) return null;

  try {
    return JSON.parse(raw) as T;
  } catch {
    window.localStorage.removeItem(key);
    return null;
  }
}

function writeJson<T>(key: string, value: T): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(key, JSON.stringify(value));
}

function clearJson(key: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(key);
}

export function readCandidateUploadState(): CandidateUploadState | null {
  return readJson<CandidateUploadState>(CANDIDATE_UPLOAD_STORAGE_KEY);
}

export function saveCandidateUploadState(state: CandidateUploadState): void {
  writeJson(CANDIDATE_UPLOAD_STORAGE_KEY, state);
}

export function clearCandidateUploadState(): void {
  clearJson(CANDIDATE_UPLOAD_STORAGE_KEY);
}

export function readRecruiterUploadState(): RecruiterUploadState | null {
  return readJson<RecruiterUploadState>(RECRUITER_UPLOAD_STORAGE_KEY);
}

export function saveRecruiterUploadState(state: RecruiterUploadState): void {
  writeJson(RECRUITER_UPLOAD_STORAGE_KEY, state);
}

export function clearRecruiterUploadState(): void {
  clearJson(RECRUITER_UPLOAD_STORAGE_KEY);
}

export function readRecruiterJobHistory(): RecruiterJobHistoryItem[] {
  return readJson<RecruiterJobHistoryItem[]>(RECRUITER_JOB_HISTORY_STORAGE_KEY) ?? [];
}

export function saveRecruiterJobHistory(history: RecruiterJobHistoryItem[]): void {
  writeJson(RECRUITER_JOB_HISTORY_STORAGE_KEY, history);
}

export function rememberRecruiterJob(entry: RecruiterJobHistoryItem): void {
  const next = [
    entry,
    ...readRecruiterJobHistory().filter((item) => item.jobId !== entry.jobId),
  ].slice(0, 20);
  saveRecruiterJobHistory(next);
}
