"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { generateExplanationFromRanking, getResults } from "@/lib/api";
import type { Candidate, CandidateStatus, ExplainabilityResponse } from "@/lib/types";

const DECISION_LABELS: Record<CandidateStatus, string> = {
  shortlist: "Shortlist",
  manual_review: "Manual Review",
  reject: "Reject",
};

const DECISION_CLASSES: Record<CandidateStatus, string> = {
  shortlist: "bg-success-100 text-success-800 border-success-200",
  manual_review: "bg-warning-100 text-warning-800 border-warning-200",
  reject: "bg-danger-100 text-danger-800 border-danger-200",
};

function DashboardContent() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get("jobId");
  const initialCandidateId = searchParams.get("candidateId");
  const jobTitle = searchParams.get("jobTitle") ?? "Applied Role";

  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(initialCandidateId);
  const [data, setData] = useState<ExplainabilityResponse | null>(null);
  const [loadingCandidates, setLoadingCandidates] = useState(false);
  const [loadingExplanation, setLoadingExplanation] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) {
      setError("Missing job ID. Open the dashboard from a real results page.");
      setCandidates([]);
      return;
    }

    let active = true;
    setLoadingCandidates(true);
    setError(null);

    getResults(jobId)
      .then((results) => {
        if (!active) return;
        setCandidates(results);
        if (!results.length) {
          setSelectedCandidateId(null);
          setError("No ranked candidates are available for this job yet.");
          return;
        }
        const selected = results.some((candidate) => candidate.id === initialCandidateId)
          ? initialCandidateId
          : results[0].id;
        setSelectedCandidateId(selected);
      })
      .catch((err: unknown) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Could not load ranked candidates.");
        setCandidates([]);
      })
      .finally(() => {
        if (active) setLoadingCandidates(false);
      });

    return () => {
      active = false;
    };
  }, [initialCandidateId, jobId]);

  const selectedCandidate = useMemo(
    () => candidates.find((candidate) => candidate.id === selectedCandidateId) ?? null,
    [candidates, selectedCandidateId],
  );

  useEffect(() => {
    if (!selectedCandidate) {
      setData(null);
      return;
    }

    let active = true;
    setLoadingExplanation(true);
    setError(null);

    generateExplanationFromRanking({
      candidate_id: selectedCandidate.id,
      candidate_name: selectedCandidate.name,
      job_title: jobTitle,
      overall_score: selectedCandidate.scoreBreakdown.overall,
      matched_skills: selectedCandidate.matchedSkills,
      missing_skills: selectedCandidate.missingSkills,
      score_breakdown: {
        skills_match: selectedCandidate.scoreBreakdown.skills,
        experience_relevance: selectedCandidate.scoreBreakdown.experience,
        education_fit: selectedCandidate.scoreBreakdown.education,
        semantic_similarity: selectedCandidate.scoreBreakdown.keywords,
      },
      jd_summary: `Real ranked candidate from job ${jobId}.`,
    })
      .then((response) => {
        if (active) setData(response);
      })
      .catch((err: unknown) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Could not load explainability data.");
        setData(null);
      })
      .finally(() => {
        if (active) setLoadingExplanation(false);
      });

    return () => {
      active = false;
    };
  }, [jobId, jobTitle, selectedCandidate]);

  return (
    <div className="page-container grid gap-6 lg:grid-cols-[280px_1fr]">
      <aside className="rounded-xl border border-neutral-200 bg-white p-4 shadow-sm">
        <p className="text-xs uppercase tracking-wider text-neutral-500">Explainability</p>
        <h1 className="mt-1 text-xl font-bold text-neutral-900">Recruiter Dashboard</h1>
        <p className="mt-2 text-sm text-neutral-500">Inspect rationale and decision signals per ranked candidate.</p>

        <div className="mt-4 space-y-2">
          {candidates.map((candidate) => (
            <button
              key={candidate.id}
              type="button"
              onClick={() => setSelectedCandidateId(candidate.id)}
              className={[
                "w-full rounded-lg border px-3 py-2 text-left transition-colors",
                selectedCandidateId === candidate.id
                  ? "border-primary-500 bg-primary-50"
                  : "border-neutral-200 bg-white hover:border-primary-300",
              ].join(" ")}
            >
              <p className="text-sm font-medium text-neutral-800">{candidate.name}</p>
              <p className="text-xs text-neutral-500">{jobTitle}</p>
            </button>
          ))}

          {!loadingCandidates && !candidates.length && (
            <p className="text-sm text-neutral-500">No real ranked candidates available yet.</p>
          )}
        </div>
      </aside>

      <main className="space-y-4">
        {(loadingCandidates || loadingExplanation) && (
          <div className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">Loading dashboard data...</div>
        )}

        {error && !loadingCandidates && !loadingExplanation && (
          <div className="rounded-xl border border-danger-200 bg-danger-50 p-4 text-danger-700">{error}</div>
        )}

        {!loadingCandidates && !loadingExplanation && data && (
          <>
            <section className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-wider text-neutral-500">Candidate Detail</p>
                  <h2 className="text-2xl font-bold text-neutral-900">{data.candidate_name}</h2>
                  <p className="text-sm text-neutral-500">{data.job_title}</p>
                </div>
                <span
                  className={[
                    "rounded-full border px-3 py-1 text-sm font-semibold",
                    DECISION_CLASSES[data.decision],
                  ].join(" ")}
                >
                  {DECISION_LABELS[data.decision]}
                </span>
              </div>

              <p className="mt-4 text-neutral-700">{data.summary}</p>

              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <Metric label="Overall Score" value={data.overall_score} />
                <Metric label="Confidence" value={data.confidence_score} />
              </div>
            </section>

            <section className="grid gap-4 md:grid-cols-2">
              <InfoList title="Strengths" items={data.strengths} />
              <InfoList title="Weaknesses" items={data.weaknesses} />
            </section>

            <section className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-neutral-500">Score Breakdown</h3>
              <div className="mt-3 space-y-3">
                {Object.entries(data.score_breakdown).map(([name, score]) => (
                  <div key={name}>
                    <div className="mb-1 flex items-center justify-between text-sm text-neutral-700">
                      <span>{name.replaceAll("_", " ")}</span>
                      <span className="font-semibold">{score}</span>
                    </div>
                    <div className="h-2 rounded-full bg-neutral-100">
                      <div
                        className="h-full rounded-full bg-primary-500"
                        style={{ width: `${Math.max(0, Math.min(100, score))}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="grid gap-4 md:grid-cols-2">
              <SkillCard title="Matched Skills" items={data.matched_skills} tone="positive" />
              <SkillCard title="Missing Skills" items={data.missing_skills} tone="negative" />
            </section>

            <section className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-neutral-500">Recommendation</h3>
              <p className="mt-2 text-neutral-700">{data.recommendation}</p>
              <h3 className="mt-4 text-sm font-semibold uppercase tracking-wider text-neutral-500">Job Context</h3>
              <p className="mt-2 text-neutral-700">{data.jd_summary}</p>
              <p className="mt-4 text-xs text-neutral-500">{data.fairness_note}</p>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<div className="page-container">Loading dashboard...</div>}>
      <DashboardContent />
    </Suspense>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-4">
      <p className="text-xs uppercase tracking-wider text-neutral-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-neutral-900">{value}</p>
    </div>
  );
}

function InfoList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
      <h3 className="text-sm font-semibold uppercase tracking-wider text-neutral-500">{title}</h3>
      <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-neutral-700">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function SkillCard({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "positive" | "negative";
}) {
  const toneClass = tone === "positive" ? "bg-success-50 text-success-700" : "bg-danger-50 text-danger-700";
  return (
    <div className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
      <h3 className="text-sm font-semibold uppercase tracking-wider text-neutral-500">{title}</h3>
      <div className="mt-3 flex flex-wrap gap-2">
        {items.map((item) => (
          <span key={item} className={`rounded-full px-2.5 py-1 text-xs font-medium ${toneClass}`}>
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}
