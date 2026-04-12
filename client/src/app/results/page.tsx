"use client";

import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { CandidateCard } from "@/components/CandidateCard";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { getResults, approveEmail } from "@/lib/api";
import type { Candidate, CandidateStatus } from "@/lib/types";

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
      if (!jobId) {
        setCandidates([]);
        setError("Missing job ID. Upload a job description first to view real rankings.");
        return;
      }

      const data = await getResults(jobId);
      setCandidates(data);
    } catch (err) {
      setCandidates([]);
      setError(err instanceof Error ? err.message : "Could not fetch real ranking results.");
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
              dashboardHref={jobId ? `/dashboard?jobId=${jobId}&candidateId=${candidate.id}` : undefined}
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
