"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { getResults, getUploadedJDs } from "@/lib/api";
import { DocumentPreview } from "@/components/ui/DocumentPreview";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { Candidate, JobDescription } from "@/lib/types";

function ReviewContent() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get("jobId");
  const candidateId = searchParams.get("candidateId");

  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [job, setJob] = useState<JobDescription | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId || !candidateId) {
      setError("Missing jobId or candidateId in URL.");
      setLoading(false);
      return;
    }

    let active = true;

    async function load() {
      try {
        const [results, jobs] = await Promise.all([
          getResults(jobId!),
          getUploadedJDs(),
        ]);
        if (!active) return;

        const found = results.find((c) => c.id === candidateId);
        const foundJob = jobs.find((j) => j.id === jobId);

        if (!found) {
          setError(`Candidate '${candidateId}' not found in results for this job.`);
        } else {
          setCandidate(found);
        }
        if (foundJob) setJob(foundJob);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Could not load review data.");
      } finally {
        if (active) setLoading(false);
      }
    }

    load();
    return () => { active = false; };
  }, [jobId, candidateId]);

  if (loading) {
    return (
      <div className="page-container">
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div key={i} className="h-[520px] animate-pulse rounded-xl bg-neutral-200" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container max-w-2xl space-y-4">
        <p className="rounded-xl bg-danger-50 border border-danger-200 px-4 py-3 text-danger-700">
          {error}
        </p>
        <Link href={jobId ? `/results?jobId=${jobId}` : "/results"}>
          <span className="text-sm text-primary-600 hover:underline">← Back to results</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="page-container space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-wider text-neutral-500">Document Review</p>
          <h1 className="text-2xl font-bold text-neutral-800">
            {candidate?.name ?? "Candidate"} — {job?.title ?? "Role"}
          </h1>
          {candidate && (
            <div className="mt-1 flex items-center gap-2">
              <StatusBadge status={candidate.status} />
              <span className="text-sm text-neutral-500">{candidate.email}</span>
            </div>
          )}
        </div>
        <div className="flex gap-2 flex-wrap">
          {jobId && candidateId && (
            <Link href={`/dashboard?jobId=${jobId}&candidateId=${candidateId}`}>
              <span className="inline-flex items-center rounded-lg border border-neutral-200 bg-white px-3 py-2 text-sm font-medium text-neutral-700 shadow-sm hover:border-primary-300 transition-colors">
                AI Analysis →
              </span>
            </Link>
          )}
          <Link href={jobId ? `/results?jobId=${jobId}` : "/results"}>
            <span className="inline-flex items-center rounded-lg border border-neutral-200 bg-white px-3 py-2 text-sm font-medium text-neutral-700 shadow-sm hover:border-primary-300 transition-colors">
              ← Back to Results
            </span>
          </Link>
        </div>
      </div>

      {/* Document Viewers */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* JD Panel */}
        <div className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm space-y-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-neutral-500">
              Job Description
            </p>
            <p className="mt-0.5 text-lg font-semibold text-neutral-800">
              {job?.title ?? "Unknown Role"}
            </p>
            {job?.id && (
              <p className="text-xs text-neutral-400">Job ID: {job.id}</p>
            )}
          </div>

          <DocumentPreview
            src={job?.fileUrl}
            title="JD Document"
            heightClass="h-[480px]"
          />
        </div>

        {/* Resume Panel */}
        <div className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm space-y-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-neutral-500">
              Resume
            </p>
            <p className="mt-0.5 text-lg font-semibold text-neutral-800">
              {candidate?.name ?? "Candidate"}
            </p>
            {candidate?.email && (
              <p className="text-xs text-neutral-400">{candidate.email}</p>
            )}
          </div>

          <DocumentPreview
            src={candidate?.resumeUrl}
            title="Resume Document"
            heightClass="h-[480px]"
          />
        </div>
      </div>

      {/* Skill Comparison */}
      {candidate && (
        <div className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm space-y-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-neutral-500">
            Skill Comparison
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <SkillGroup
              title="Matched Skills"
              skills={candidate.matchedSkills}
              chipClass="bg-success-100 text-success-700 border-success-200"
              emptyText="No matched skills recorded"
            />
            <SkillGroup
              title="Missing Skills"
              skills={candidate.missingSkills}
              chipClass="bg-danger-100 text-danger-700 border-danger-200"
              emptyText="No missing skills recorded"
            />
          </div>
        </div>
      )}

      {/* Score Overview */}
      {candidate && (
        <div className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm space-y-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-neutral-500">
            Score Overview
          </h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <ScoreBar label="Skills"     value={candidate.scoreBreakdown.skills} />
            <ScoreBar label="Experience" value={candidate.scoreBreakdown.experience} />
            <ScoreBar label="Education"  value={candidate.scoreBreakdown.education} />
            <ScoreBar label="Keywords"   value={candidate.scoreBreakdown.keywords} />
          </div>
          <div className="mt-2 flex items-center gap-3 rounded-lg bg-primary-50 border border-primary-100 px-4 py-3">
            <span className="text-sm font-medium text-primary-700">Overall Score</span>
            <span className="ml-auto text-2xl font-bold text-primary-700">
              {candidate.scoreBreakdown.overall}
              <span className="text-sm font-normal text-primary-400"> / 100</span>
            </span>
          </div>
        </div>
      )}

      {/* AI Explanation */}
      {candidate?.explanation && (
        <div className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm space-y-2">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-neutral-500">
            AI Explanation
          </h2>
          <p className="text-sm leading-relaxed text-neutral-700">{candidate.explanation}</p>
        </div>
      )}
    </div>
  );
}

export default function ReviewPage() {
  return (
    <Suspense fallback={
      <div className="page-container space-y-4">
        {[1, 2].map((i) => (
          <div key={i} className="h-[520px] animate-pulse rounded-xl bg-neutral-200" />
        ))}
      </div>
    }>
      <ReviewContent />
    </Suspense>
  );
}

function SkillGroup({
  title,
  skills,
  chipClass,
  emptyText,
}: {
  title: string;
  skills: string[];
  chipClass: string;
  emptyText: string;
}) {
  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold uppercase tracking-wider text-neutral-500">{title}</p>
      {skills.length === 0 ? (
        <p className="text-xs text-neutral-400">{emptyText}</p>
      ) : (
        <div className="flex flex-wrap gap-1.5">
          {skills.map((skill) => (
            <span
              key={skill}
              className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${chipClass}`}
            >
              {skill}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs text-neutral-600">
        <span>{label}</span>
        <span className="font-semibold">{value}</span>
      </div>
      <div className="h-2 rounded-full bg-neutral-100">
        <div
          className="h-full rounded-full bg-primary-500 transition-all"
          style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
        />
      </div>
    </div>
  );
}
