"use client";

import { useState } from "react";
import { FileUpload } from "@/components/ui/FileUpload";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { PipelineStatus } from "@/components/PipelineStatus";
import { uploadResume } from "@/lib/api";
import type { PipelineStage } from "@/lib/types";

const INITIAL_STAGES: PipelineStage[] = [
  { label: "Upload",  status: "pending" },
  { label: "Parse",   status: "pending" },
  { label: "Embed",   status: "pending" },
  { label: "Queue",   status: "pending" },
];

export default function CandidatePage() {
  const [file, setFile]       = useState<File | null>(null);
  const [email, setEmail]     = useState("");
  const [name, setName]       = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);
  const [done, setDone]       = useState(false);
  const [stages, setStages]   = useState<PipelineStage[]>(INITIAL_STAGES);

  function updateStage(idx: number, status: PipelineStage["status"]) {
    setStages((prev) =>
      prev.map((s, i) => (i === idx ? { ...s, status } : s))
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !email.trim() || !name.trim()) return;

    setLoading(true);
    setError(null);

    try {
      updateStage(0, "processing");
      await uploadResume(file, email.trim(), name.trim());
      updateStage(0, "done");

      for (let i = 1; i < INITIAL_STAGES.length; i++) {
        updateStage(i, "processing");
        await delay(700);
        updateStage(i, "done");
      }

      setDone(true);
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

          <FileUpload
            label="Resume"
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
            disabled={!file || !email.trim() || !name.trim()}
            className="w-full"
            size="lg"
          >
            Submit Resume
          </Button>
        </form>
      </Card>

      {loading && <PipelineStatus stages={stages} />}
    </div>
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

function delay(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}
