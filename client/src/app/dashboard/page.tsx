"use client";

import { useEffect, useState } from "react";
import { generateExplanation } from "@/lib/api";
import type { CandidateStatus, ExplainabilityResponse } from "@/lib/types";

const CANDIDATES = [
  { candidate_id: "CAND-001", candidate_name: "Aarav Mehta", job_title: "Machine Learning Engineer" },
  { candidate_id: "CAND-002", candidate_name: "Tanay Shirodkar", job_title: "Machine Learning Engineer" },
  { candidate_id: "CAND-003", candidate_name: "Rohan Singh", job_title: "Machine Learning Engineer" },
];

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

export default function DashboardPage() {
  const [selectedCandidateId, setSelectedCandidateId] = useState(CANDIDATES[0].candidate_id);
  const [data, setData] = useState<ExplainabilityResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    generateExplanation(selectedCandidateId)
      .then((response) => {
        if (active) setData(response);
      })
      .catch((err: unknown) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Could not load explainability data.");
        setData(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [selectedCandidateId]);

  return (
    <div className="page-container grid gap-6 lg:grid-cols-[280px_1fr]">
      <aside className="rounded-xl border border-neutral-200 bg-white p-4 shadow-sm">
        <p className="text-xs uppercase tracking-wider text-neutral-500">Explainability</p>
        <h1 className="mt-1 text-xl font-bold text-neutral-900">Recruiter Dashboard</h1>
        <p className="mt-2 text-sm text-neutral-500">Inspect rationale and decision signals per candidate.</p>

        <div className="mt-4 space-y-2">
          {CANDIDATES.map((candidate) => (
            <button
              key={candidate.candidate_id}
              type="button"
              onClick={() => setSelectedCandidateId(candidate.candidate_id)}
              className={[
                "w-full rounded-lg border px-3 py-2 text-left transition-colors",
                selectedCandidateId === candidate.candidate_id
                  ? "border-primary-500 bg-primary-50"
                  : "border-neutral-200 bg-white hover:border-primary-300",
              ].join(" ")}
            >
              <p className="text-sm font-medium text-neutral-800">{candidate.candidate_name}</p>
              <p className="text-xs text-neutral-500">{candidate.job_title}</p>
            </button>
          ))}
        </div>
      </aside>

      <main className="space-y-4">
        {loading && (
          <div className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">Loading dashboard data...</div>
        )}

        {error && !loading && (
          <div className="rounded-xl border border-danger-200 bg-danger-50 p-4 text-danger-700">{error}</div>
        )}

        {!loading && data && (
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
