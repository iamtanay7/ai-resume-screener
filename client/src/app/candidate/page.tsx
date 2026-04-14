"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { FileUpload } from "@/components/ui/FileUpload";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { PipelineStatus } from "@/components/PipelineStatus";
import { getResumeStatus, getUploadedJDs, uploadResume } from "@/lib/api";
import {
  clearCandidateUploadState,
  readCandidateUploadState,
  saveCandidateUploadState,
} from "@/lib/persistence";
import type { BackendProcessingStatus, JobDescription, PipelineStage } from "@/lib/types";
import { DocumentPreview } from "@/components/ui/DocumentPreview";

const INITIAL_STAGES: PipelineStage[] = [
  { label: "Upload",  status: "pending" },
  { label: "Parse",   status: "pending" },
  { label: "Embed",   status: "pending" },
  { label: "Queue",   status: "pending" },
];

function CandidatePageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [file, setFile]       = useState<File | null>(null);
  const [email, setEmail]     = useState("");
  const [name, setName]       = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);
  const [done, setDone]       = useState(false);
  const [stages, setStages]   = useState<PipelineStage[]>(INITIAL_STAGES);
  const [candidateId, setCandidateId] = useState<string | null>(null);
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [jobsLoading, setJobsLoading] = useState(true);
  const [jobId, setJobId] = useState<string>("");
  const pollRef = useRef<number | null>(null);
  const jobsAvailable = !jobsLoading && jobs.length > 0;

  useEffect(() => {
    const candidateIdFromUrl = searchParams.get("candidateId");
    const persisted = readCandidateUploadState();

    if (candidateIdFromUrl) {
      setCandidateId(candidateIdFromUrl);
      if (persisted?.candidateId === candidateIdFromUrl) {
        setName(persisted.name);
        setEmail(persisted.email);
        setJobId(persisted.jobId);
      }
      return;
    }

    if (persisted) {
      setCandidateId(persisted.candidateId);
      setName(persisted.name);
      setEmail(persisted.email);
      setJobId(persisted.jobId);
      router.replace(`/candidate?candidateId=${persisted.candidateId}`);
    }
  }, [router, searchParams]);

  useEffect(() => {
    let cancelled = false;

    async function loadJobs() {
      setJobsLoading(true);
      try {
        const data = await getUploadedJDs();
        if (!cancelled) setJobs(data);
      } catch {
        if (!cancelled) setJobs([]);
      } finally {
        if (!cancelled) setJobsLoading(false);
      }
    }

    loadJobs();
    return () => {
      cancelled = true;
    };
  }, []);

  function updateStage(idx: number, status: PipelineStage["status"]) {
    setStages((prev) =>
      prev.map((s, i) => (i === idx ? { ...s, status } : s))
    );
  }

  useEffect(() => {
    if (!candidateId) return;

    let cancelled = false;
    const currentCandidateId = candidateId;

    async function poll() {
      try {
        const status = await getResumeStatus(currentCandidateId);
        if (cancelled) return;

        setStages(mapResumeStages(status.status));

        if (status.status === "failed") {
          setError(status.processingError ?? "Processing failed");
          setLoading(false);
          return;
        }

        if (status.status === "processed") {
          setDone(true);
          saveCandidateUploadState({
            candidateId: currentCandidateId,
            name,
            email,
            jobId,
          });
          setLoading(false);
          return;
        }

        pollRef.current = window.setTimeout(poll, 1500);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Could not fetch status");
        setLoading(false);
      }
    }

    poll();

    return () => {
      cancelled = true;
      if (pollRef.current) {
        window.clearTimeout(pollRef.current);
      }
    };
  }, [candidateId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !email.trim() || !name.trim() || !jobId) return;

    setLoading(true);
    setError(null);

    try {
      updateStage(0, "processing");
      const { candidateId } = await uploadResume(file, email.trim(), name.trim(), jobId);
      updateStage(0, "done");
      setCandidateId(candidateId);
      saveCandidateUploadState({
        candidateId,
        name: name.trim(),
        email: email.trim(),
        jobId,
      });
      router.replace(`/candidate?candidateId=${candidateId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setStages((prev) =>
        prev.map((s) => (s.status === "processing" ? { ...s, status: "error" } : s))
      );
    } finally {
      setLoading(false);
    }
  }

  if (done) {
    return (
      <div className="page-container max-w-2xl space-y-6">
        <div className="text-center space-y-3 pt-8">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-success-100 text-3xl">
            ✓
          </div>
          <h2 className="text-2xl font-bold text-neutral-800">Resume Submitted!</h2>
          <p className="text-neutral-500">
            We&apos;ve received your resume, {name}. Our AI is processing it now.
            You&apos;ll receive an email at <strong>{email}</strong> once the recruiter
            reviews the results.
          </p>
        </div>
        <PipelineStatus stages={stages} />
        <div className="flex justify-center">
          <Button
            variant="secondary"
            onClick={() => {
              setDone(false);
              setStages(INITIAL_STAGES);
              setFile(null);
              setEmail("");
              setName("");
              setJobId("");
              setCandidateId(null);
              setError(null);
              clearCandidateUploadState();
              router.replace("/candidate");
            }}
          >
            Submit Another Resume
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container max-w-2xl space-y-8">
      <div>
        <h1 className="section-heading">Submit Your Resume</h1>
        <p className="section-sub mt-1">
          Upload your resume to be matched against open roles. We&apos;ll email you
          when the recruiter reviews the results.
        </p>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-6">
          <TextField
            id="name"
            label="Full Name"
            value={name}
            onChange={setName}
            placeholder="Jane Smith"
            required
          />

          <TextField
            id="email"
            label="Email Address"
            type="email"
            value={email}
            onChange={setEmail}
            placeholder="jane@example.com"
            required
          />

          <div className="space-y-1.5">
            <label htmlFor="jobId" className="text-sm font-medium text-neutral-700">
              Apply To Job
            </label>
            <select
              id="jobId"
              value={jobId}
              onChange={(e) => setJobId(e.target.value)}
              required
              className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm text-neutral-800 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 transition-colors"
            >
              <option value="" disabled>
                {jobsLoading
                  ? "Loading jobs..."
                  : jobsAvailable
                    ? "Select a job"
                    : "No jobs available"}
              </option>
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title || "Untitled role"}
                </option>
              ))}
            </select>
            {!jobsLoading && !jobsAvailable && (
              <p className="text-xs text-neutral-500">
                A recruiter needs to upload a job description before you can apply.
              </p>
            )}
          </div>

          <FileUpload
            label="Resume"
            accept=".pdf,.docx"
            onFile={setFile}
            hint="PDF or DOCX — max 10 MB"
          />

          {file && (
            <DocumentPreview
              file={file}
              title="Resume Preview"
              heightClass="h-[420px]"
            />
          )}

          {error && (
            <p className="rounded-lg bg-danger-50 border border-danger-200 px-3 py-2 text-sm text-danger-700">
              {error}
            </p>
          )}

          <Button
            type="submit"
            loading={loading}
            disabled={!file || !email.trim() || !name.trim() || !jobId || !jobsAvailable}
            className="w-full"
            size="lg"
          >
            Submit Resume
          </Button>
        </form>
      </Card>

      {loading && <PipelineStatus stages={stages} />}

      {candidateId && !loading && <PipelineStatus stages={stages} />}
    </div>
  );
}

export default function CandidatePage() {
  return (
    <Suspense fallback={<div className="page-container max-w-2xl" />}>
      <CandidatePageContent />
    </Suspense>
  );
}

function TextField({
  id,
  label,
  value,
  onChange,
  placeholder,
  type = "text",
  required,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
  required?: boolean;
}) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="text-sm font-medium text-neutral-700">
        {label}
      </label>
      <input
        id={id}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm text-neutral-800 placeholder:text-neutral-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 transition-colors"
      />
    </div>
  );
}

function mapResumeStages(status: BackendProcessingStatus): PipelineStage[] {
  if (status === "failed") {
    return [
      { label: "Upload", status: "done" },
      { label: "Parse", status: "error" },
      { label: "Embed", status: "pending" },
      { label: "Queue", status: "pending" },
    ];
  }

  if (status === "uploaded") {
    return [
      { label: "Upload", status: "done" },
      { label: "Parse", status: "pending" },
      { label: "Embed", status: "pending" },
      { label: "Queue", status: "pending" },
    ];
  }

  if (status === "parsing") {
    return [
      { label: "Upload", status: "done" },
      { label: "Parse", status: "processing" },
      { label: "Embed", status: "pending" },
      { label: "Queue", status: "pending" },
    ];
  }

  if (status === "parsed") {
    return [
      { label: "Upload", status: "done" },
      { label: "Parse", status: "done" },
      { label: "Embed", status: "pending" },
      { label: "Queue", status: "processing" },
    ];
  }

  if (status === "embedding") {
    return [
      { label: "Upload", status: "done" },
      { label: "Parse", status: "done" },
      { label: "Embed", status: "processing" },
      { label: "Queue", status: "pending" },
    ];
  }

  return [
    { label: "Upload", status: "done" },
    { label: "Parse", status: "done" },
    { label: "Embed", status: "done" },
    { label: "Queue", status: "done" },
  ];
}
