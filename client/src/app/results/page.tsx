"use client";

import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { CandidateCard } from "@/components/CandidateCard";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { getResults, approveEmail } from "@/lib/api";
import type { Candidate, CandidateStatus } from "@/lib/types";

// ── mock data for dev (no backend yet) ──────────────────────────────────────
const MOCK_CANDIDATES: Candidate[] = [
  {
    id: "c1", rank: 1, name: "Alice Chen", email: "alice@example.com",
    resumeUrl: "#", status: "shortlist",
    scoreBreakdown: { skills: 92, experience: 88, education: 85, keywords: 90, overall: 90 },
    explanation:
      "Alice closely matches all required skills including Python, TensorFlow, and MLOps. She has 5 years of relevant ML engineering experience which exceeds the 3-year requirement, and holds an MS in Computer Science from a top institution.",
    matchedSkills: ["Python", "TensorFlow", "MLOps", "Docker", "Kubernetes", "GCP"],
    missingSkills: ["Spark"],
  },
  {
    id: "c2", rank: 2, name: "Ben Okafor", email: "ben@example.com",
    resumeUrl: "#", status: "shortlist",
    scoreBreakdown: { skills: 80, experience: 75, education: 78, keywords: 82, overall: 79 },
    explanation:
      "Ben demonstrates strong Python and deep learning skills. His 3 years of experience meets the minimum requirement. Minor gaps in cloud infrastructure tools are noted.",
    matchedSkills: ["Python", "PyTorch", "REST APIs", "SQL"],
    missingSkills: ["Kubernetes", "MLOps", "Spark"],
  },
  {
    id: "c3", rank: 3, name: "Priya Nair", email: "priya@example.com",
    resumeUrl: "#", status: "manual_review",
    scoreBreakdown: { skills: 65, experience: 60, education: 90, keywords: 70, overall: 67 },
    explanation:
      "Priya has an exceptional academic background with a PhD in Statistics, but her industry experience is limited to 1 year — below the 3-year minimum. Her strong fundamentals suggest high potential; recommend manual review.",
    matchedSkills: ["Python", "R", "Statistics", "Machine Learning"],
    missingSkills: ["MLOps", "Kubernetes", "Docker", "GCP", "Production deployment"],
  },
  {
    id: "c4", rank: 4, name: "Carlos Ruiz", email: "carlos@example.com",
    resumeUrl: "#", status: "reject",
    scoreBreakdown: { skills: 35, experience: 40, education: 50, keywords: 30, overall: 38 },
    explanation:
      "Carlos's background is primarily in frontend development with minimal ML experience. The required skills such as TensorFlow, model training, and cloud ML platforms are absent from the resume.",
    matchedSkills: ["JavaScript", "React"],
    missingSkills: ["Python", "TensorFlow", "MLOps", "Cloud platforms", "Model training"],
  },
];

const STATUS_FILTERS: { label: string; value: CandidateStatus | "all" }[] = [
  { label: "All",           value: "all" },
  { label: "Shortlisted",   value: "shortlist" },
  { label: "Manual Review", value: "manual_review" },
  { label: "Rejected",      value: "reject" },
];

function ResultsContent() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get("jobId");

  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState<string | null>(null);
  const [filter, setFilter]         = useState<CandidateStatus | "all">("all");

  const fetchResults = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (jobId) {
        const data = await getResults(jobId);
        setCandidates(data);
      } else {
        // Dev mode: use mock data when no jobId
        await delay(800);
        setCandidates(MOCK_CANDIDATES);
      }
    } catch {
      // Fall back to mock data if backend unreachable
      setCandidates(MOCK_CANDIDATES);
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => { fetchResults(); }, [fetchResults]);

  const filtered = filter === "all"
    ? candidates
    : candidates.filter((c) => c.status === filter);

  const counts = {
    shortlist:     candidates.filter((c) => c.status === "shortlist").length,
    manual_review: candidates.filter((c) => c.status === "manual_review").length,
    reject:        candidates.filter((c) => c.status === "reject").length,
  };

  if (loading) return <LoadingSkeleton />;
  if (error) return (
    <div className="page-container">
      <p className="rounded-xl bg-danger-50 border border-danger-200 px-4 py-3 text-danger-700">
        {error}
      </p>
      <Button variant="secondary" className="mt-4" onClick={fetchResults}>Retry</Button>
    </div>
  );

  return (
    <div className="page-container space-y-8">
      {/* Page header */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="section-heading">Candidate Rankings</h1>
          {jobId && (
            <p className="section-sub mt-0.5 text-xs">Job ID: {jobId}</p>
          )}
        </div>
        <Button variant="secondary" size="sm" onClick={fetchResults}>
          Refresh
        </Button>
      </div>

      {/* Summary pills */}
      <div className="flex flex-wrap gap-3">
        <SummaryPill label="Shortlisted"   count={counts.shortlist}     status="shortlist" />
        <SummaryPill label="Manual Review" count={counts.manual_review} status="manual_review" />
        <SummaryPill label="Rejected"      count={counts.reject}        status="reject" />
      </div>

      {/* Filter tabs */}
      <div className="flex flex-wrap gap-2">
        {STATUS_FILTERS.map(({ label, value }) => (
          <button
            key={value}
            onClick={() => setFilter(value)}
            className={[
              "rounded-full px-3 py-1 text-sm font-medium border transition-colors",
              filter === value
                ? "bg-primary-600 text-white border-primary-600"
                : "bg-white text-neutral-600 border-neutral-200 hover:border-primary-300",
            ].join(" ")}
          >
            {label}
            <span className="ml-1.5 text-xs opacity-70">
              {value === "all" ? candidates.length : candidates.filter((c) => c.status === value).length}
            </span>
          </button>
        ))}
      </div>

      {/* Candidate list */}
      {filtered.length === 0 ? (
        <p className="text-center text-neutral-400 py-12">No candidates in this category.</p>
      ) : (
        <div className="space-y-4">
          {filtered.map((candidate) => (
            <CandidateCard
              key={candidate.id}
              candidate={candidate}
              onApproveEmail={approveEmail}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function ResultsPage() {
  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <ResultsContent />
    </Suspense>
  );
}

function SummaryPill({
  label,
  count,
  status,
}: {
  label: string;
  count: number;
  status: CandidateStatus;
}) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-neutral-200 bg-white px-4 py-2 shadow-sm">
      <StatusBadge status={status} />
      <span className="text-lg font-bold text-neutral-800">{count}</span>
      <span className="text-sm text-neutral-500">{label}</span>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="page-container space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-28 animate-pulse rounded-xl bg-neutral-200" />
      ))}
    </div>
  );
}

function delay(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}
