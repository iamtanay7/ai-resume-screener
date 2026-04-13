"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { FileUpload } from "@/components/ui/FileUpload";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { PipelineStatus } from "@/components/PipelineStatus";
import { getJDStatus, getUploadedJDs, uploadJD } from "@/lib/api";
import {
  clearRecruiterUploadState,
  rememberRecruiterJob,
  readRecruiterJobHistory,
  readRecruiterUploadState,
  saveRecruiterUploadState,
} from "@/lib/persistence";
import type { BackendProcessingStatus, JobDescription, PipelineStage } from "@/lib/types";

const INITIAL_STAGES: PipelineStage[] = [
  { label: "Upload",    status: "pending" },
  { label: "Parse",     status: "pending" },
  { label: "Embed",     status: "pending" },
  { label: "Index",     status: "pending" },
];

function RecruiterPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [file, setFile]       = useState<File | null>(null);
  const [jobTitle, setJobTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);
  const [jobId, setJobId]     = useState<string | null>(null);
  const [stages, setStages]   = useState<PipelineStage[]>(INITIAL_STAGES);
  const [jobs, setJobs]       = useState<JobDescription[]>([]);
  const [jobsLoading, setJobsLoading] = useState(true);
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    const jobIdFromUrl = searchParams.get("jobId");
    const persisted = readRecruiterUploadState();

    if (jobIdFromUrl) {
      setJobId(jobIdFromUrl);
      if (persisted?.jobId === jobIdFromUrl) {
        setJobTitle(persisted.jobTitle);
      }
      return;
    }

    if (persisted) {
      setJobId(persisted.jobId);
      setJobTitle(persisted.jobTitle);
      router.replace(`/recruiter?jobId=${persisted.jobId}`);
    }
  }, [router, searchParams]);

  useEffect(() => {
    let cancelled = false;

    async function loadJobs() {
      setJobsLoading(true);
      try {
        const backendJobs = await getUploadedJDs();
        if (cancelled) return;
        const history = readRecruiterJobHistory();
        const historyTitles = new Map(history.map((item) => [item.jobId, item.jobTitle]));
        setJobs(
          backendJobs.map((job) => ({
            ...job,
            title: job.title || historyTitles.get(job.id) || "Untitled role",
          }))
        );
      } catch {
        if (cancelled) return;
      } finally {
        if (!cancelled) setJobsLoading(false);
      }
    }

    loadJobs();
    return () => {
      cancelled = true;
    };
  }, [jobId]);

  function updateStage(idx: number, status: PipelineStage["status"]) {
    setStages((prev) =>
      prev.map((s, i) => (i === idx ? { ...s, status } : s))
    );
  }

  useEffect(() => {
    if (!jobId) return;

    let cancelled = false;
    const currentJobId = jobId;

    async function poll() {
      try {
        const status = await getJDStatus(currentJobId);
        if (cancelled) return;

        setStages(mapJDStages(status.status));

        if (status.status === "failed") {
          setError(status.processingError ?? "Processing failed");
          setLoading(false);
          return;
        }

        if (status.status === "processed") {
          setLoading(false);
          saveRecruiterUploadState({
            jobId: currentJobId,
            jobTitle,
          });
          setJobs((prev) =>
            prev.map((job) =>
              job.id === currentJobId ? { ...job, status: "processed", processingError: null } : job
            )
          );
          return;
        }

        setJobs((prev) =>
          prev.map((job) =>
            job.id === currentJobId
              ? { ...job, status: status.status, processingError: status.processingError }
              : job
          )
        );

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
  }, [jobId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !jobTitle.trim()) return;

    setLoading(true);
    setError(null);

    try {
      updateStage(0, "processing");
      const { jobId: id } = await uploadJD(file, jobTitle.trim());
      updateStage(0, "done");
      setJobId(id);
      saveRecruiterUploadState({
        jobId: id,
        jobTitle: jobTitle.trim(),
      });
      rememberRecruiterJob({
        jobId: id,
        jobTitle: jobTitle.trim(),
      });
      setJobs((prev) => [
        {
          id,
          title: jobTitle.trim(),
          fileUrl: "",
          uploadedAt: new Date().toISOString(),
          status: "uploaded",
          processingError: null,
        },
        ...prev.filter((job) => job.id !== id),
      ]);
      setFile(null);
      router.replace(`/recruiter?jobId=${id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setStages((prev) =>
        prev.map((s) => (s.status === "processing" ? { ...s, status: "error" } : s))
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-container max-w-2xl space-y-8">
      <div>
        <h1 className="section-heading">Upload Job Description</h1>
        <p className="section-sub mt-1">
          Upload a JD and we&apos;ll rank all incoming resumes against it automatically.
        </p>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-1.5">
            <label htmlFor="jobTitle" className="text-sm font-medium text-neutral-700">
              Job Title
            </label>
            <input
              id="jobTitle"
              type="text"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              placeholder="e.g. Senior Machine Learning Engineer"
              required
              className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm text-neutral-800 placeholder:text-neutral-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 transition-colors"
            />
          </div>

          <FileUpload
            label="Job Description File"
            accept=".pdf"
            onFile={setFile}
            hint="PDF only — max 10 MB"
          />

          {error && (
            <p className="rounded-lg bg-danger-50 border border-danger-200 px-3 py-2 text-sm text-danger-700">
              {error}
            </p>
          )}

          <Button
            type="submit"
            loading={loading}
            disabled={!file || !jobTitle.trim()}
            className="w-full"
            size="lg"
          >
            Upload & Process JD
          </Button>
        </form>
      </Card>

      {jobId && (
        <div className="space-y-4">
          <SuccessBanner title="Latest job description uploaded" />
          <PipelineStatus stages={stages} />
          <div className="flex justify-end gap-3">
            <Button
              variant="secondary"
              onClick={() => {
                setJobId(null);
                setStages(INITIAL_STAGES);
                setJobTitle("");
                setError(null);
                clearRecruiterUploadState();
                router.replace("/recruiter");
              }}
            >
              Clear Current View
            </Button>
            <Button onClick={() => router.push(`/results?jobId=${jobId}`)}>
              View Latest Results →
            </Button>
          </div>
        </div>
      )}

      {(loading || jobId) && (
        <PipelineStatus stages={stages} />
      )}

      <Card className="space-y-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-neutral-800">Uploaded Job Descriptions</h2>
            <p className="text-sm text-neutral-500">
              Recruiters can manage multiple roles and open rankings for each one separately.
            </p>
          </div>
        </div>

        {jobsLoading ? (
          <p className="text-sm text-neutral-500">Loading uploaded roles...</p>
        ) : jobs.length === 0 ? (
          <p className="text-sm text-neutral-500">No job descriptions uploaded yet.</p>
        ) : (
          <div className="space-y-3">
            {jobs.map((job) => (
              <div
                key={job.id}
                className="rounded-xl border border-neutral-200 bg-white px-4 py-3 shadow-sm"
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="space-y-1">
                    <p className="font-medium text-neutral-800">{job.title}</p>
                    <p className="text-xs text-neutral-500">Job ID: {job.id}</p>
                    <p className="text-xs text-neutral-500">
                      Uploaded: {new Date(job.uploadedAt).toLocaleString()}
                    </p>
                    <p className="text-sm text-neutral-600">
                      Status: <span className="font-medium">{humanizeStatus(job.status)}</span>
                    </p>
                    {job.processingError && (
                      <p className="text-sm text-danger-700">{job.processingError}</p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      onClick={() => {
                        setJobId(job.id);
                        setJobTitle(job.title);
                        saveRecruiterUploadState({ jobId: job.id, jobTitle: job.title });
                        router.push(`/recruiter?jobId=${job.id}`);
                      }}
                    >
                      Track Status
                    </Button>
                    <Button onClick={() => router.push(`/results?jobId=${job.id}`)}>
                      View Rankings
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

export default function RecruiterPage() {
  return (
    <Suspense fallback={<div className="page-container max-w-2xl" />}>
      <RecruiterPageContent />
    </Suspense>
  );
}

function SuccessBanner({ title }: { title: string }) {
  return (
    <div className="flex items-center gap-3 rounded-xl bg-success-50 border border-success-200 px-4 py-3">
      <span className="text-success-500 text-xl">✓</span>
      <p className="font-medium text-success-800">{title}</p>
    </div>
  );
}

function mapJDStages(status: BackendProcessingStatus): PipelineStage[] {
  if (status === "failed") {
    return [
      { label: "Upload", status: "done" },
      { label: "Parse", status: "error" },
      { label: "Embed", status: "pending" },
      { label: "Index", status: "pending" },
    ];
  }

  if (status === "uploaded") {
    return [
      { label: "Upload", status: "done" },
      { label: "Parse", status: "pending" },
      { label: "Embed", status: "pending" },
      { label: "Index", status: "pending" },
    ];
  }

  if (status === "parsing") {
    return [
      { label: "Upload", status: "done" },
      { label: "Parse", status: "processing" },
      { label: "Embed", status: "pending" },
      { label: "Index", status: "pending" },
    ];
  }

  if (status === "parsed") {
    return [
      { label: "Upload", status: "done" },
      { label: "Parse", status: "done" },
      { label: "Embed", status: "pending" },
      { label: "Index", status: "processing" },
    ];
  }

  if (status === "embedding") {
    return [
      { label: "Upload", status: "done" },
      { label: "Parse", status: "done" },
      { label: "Embed", status: "processing" },
      { label: "Index", status: "pending" },
    ];
  }

  return [
    { label: "Upload", status: "done" },
    { label: "Parse", status: "done" },
    { label: "Embed", status: "done" },
    { label: "Index", status: "done" },
  ];
}

function humanizeStatus(status: string): string {
  return status
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
