"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FileUpload } from "@/components/ui/FileUpload";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { PipelineStatus } from "@/components/PipelineStatus";
import { uploadJD } from "@/lib/api";
import type { PipelineStage } from "@/lib/types";

const INITIAL_STAGES: PipelineStage[] = [
  { label: "Upload",    status: "pending" },
  { label: "Parse",     status: "pending" },
  { label: "Embed",     status: "pending" },
  { label: "Index",     status: "pending" },
];

export default function RecruiterPage() {
  const router = useRouter();
  const [file, setFile]       = useState<File | null>(null);
  const [jobTitle, setJobTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);
  const [jobId, setJobId]     = useState<string | null>(null);
  const [stages, setStages]   = useState<PipelineStage[]>(INITIAL_STAGES);

  function updateStage(idx: number, status: PipelineStage["status"]) {
    setStages((prev) =>
      prev.map((s, i) => (i === idx ? { ...s, status } : s))
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !jobTitle.trim()) return;

    setLoading(true);
    setError(null);

    try {
      updateStage(0, "processing");
      const { jobId: id } = await uploadJD(file, jobTitle.trim());
      updateStage(0, "done");

      // Simulate downstream pipeline stages (real status comes from Firestore polling in prod)
      for (let i = 1; i < INITIAL_STAGES.length; i++) {
        updateStage(i, "processing");
        await delay(800);
        updateStage(i, "done");
      }

      setJobId(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setStages((prev) =>
        prev.map((s) => (s.status === "processing" ? { ...s, status: "error" } : s))
      );
    } finally {
      setLoading(false);
    }
  }

  if (jobId) {
    return (
      <div className="page-container max-w-2xl space-y-6">
        <SuccessBanner title="Job Description uploaded!" />
        <PipelineStatus stages={stages} />
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={() => { setJobId(null); setStages(INITIAL_STAGES); setFile(null); setJobTitle(""); }}>
            Upload Another
          </Button>
          <Button onClick={() => router.push(`/results?jobId=${jobId}`)}>
            View Results →
          </Button>
        </div>
      </div>
    );
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
            accept=".pdf,.docx"
            onFile={setFile}
            hint="PDF or DOCX — max 10 MB"
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

      {loading && (
        <PipelineStatus stages={stages} />
      )}
    </div>
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

function delay(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}
