"use client";

import Link from "next/link";
import { useState } from "react";
import type { Candidate } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ScoreBreakdown } from "@/components/ScoreBreakdown";

interface CandidateCardProps {
  candidate: Candidate;
  onApproveEmail: (candidateId: string) => Promise<void>;
  dashboardHref?: string;
}

export function CandidateCard({ candidate, onApproveEmail, dashboardHref }: CandidateCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [approving, setApproving] = useState(false);
  const [approved, setApproved] = useState(false);

  async function handleApprove() {
    setApproving(true);
    try {
      await onApproveEmail(candidate.id);
      setApproved(true);
    } finally {
      setApproving(false);
    }
  }

  return (
    <Card className="animate-fade-in">
      {/* Header row */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-100 text-sm font-bold text-primary-700">
            #{candidate.rank}
          </div>
          <div>
            <p className="font-semibold text-neutral-800">{candidate.name}</p>
            <p className="text-sm text-neutral-500">{candidate.email}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <StatusBadge status={candidate.status} />
          <div className="text-right">
            <p className="text-xl font-bold text-primary-700">
              {candidate.scoreBreakdown.overall}
            </p>
            <p className="text-xs text-neutral-400">/ 100</p>
          </div>
        </div>
      </div>

      {/* Matched / missing skills summary */}
      <div className="mt-4 flex gap-6 text-xs text-neutral-500">
        <span>
          <span className="font-medium text-success-600">
            {candidate.matchedSkills.length}
          </span>{" "}
          skills matched
        </span>
        <span>
          <span className="font-medium text-danger-600">
            {candidate.missingSkills.length}
          </span>{" "}
          skills missing
        </span>
      </div>

      {/* Expand toggle */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="mt-4 flex w-full items-center justify-between rounded-lg bg-neutral-50 px-3 py-2 text-xs font-medium text-neutral-600 hover:bg-neutral-100 transition-colors"
      >
        <span>View details</span>
        <ChevronIcon expanded={expanded} />
      </button>

      {/* Expandable section */}
      {expanded && (
        <div className="mt-4 space-y-5 animate-fade-in">
          <ScoreBreakdown scoreBreakdown={candidate.scoreBreakdown} />

          {/* Gemini explanation */}
          <div className="space-y-1.5">
            <p className="text-xs font-semibold uppercase tracking-wider text-neutral-500">
              AI Explanation
            </p>
            <p className="rounded-lg bg-neutral-50 p-3 text-sm leading-relaxed text-neutral-700">
              {candidate.explanation}
            </p>
          </div>

          {/* Matched skills */}
          {candidate.matchedSkills.length > 0 && (
            <SkillList
              title="Matched Skills"
              skills={candidate.matchedSkills}
              chipClass="bg-success-100 text-success-700 border-success-200"
            />
          )}

          {/* Missing skills */}
          {candidate.missingSkills.length > 0 && (
            <SkillList
              title="Missing Skills"
              skills={candidate.missingSkills}
              chipClass="bg-danger-100 text-danger-700 border-danger-200"
            />
          )}

          {/* Approve email CTA */}
          {(candidate.status !== "reject" || dashboardHref) && (
            <div className="flex justify-end gap-2">
              {dashboardHref && (
                <Link href={dashboardHref}>
                  <Button variant="secondary" size="sm">
                    View Dashboard
                  </Button>
                </Link>
              )}
              <Button
                variant={approved ? "secondary" : "primary"}
                size="sm"
                loading={approving}
                disabled={approved}
                onClick={handleApprove}
              >
                {approved ? "Email Approved ✓" : "Approve Email"}
              </Button>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

function SkillList({
  title,
  skills,
  chipClass,
}: {
  title: string;
  skills: string[];
  chipClass: string;
}) {
  return (
    <div className="space-y-1.5">
      <p className="text-xs font-semibold uppercase tracking-wider text-neutral-500">
        {title}
      </p>
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
    </div>
  );
}

function ChevronIcon({ expanded }: { expanded: boolean }) {
  return (
    <svg
      className={`h-4 w-4 transition-transform duration-200 ${expanded ? "rotate-180" : ""}`}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
    </svg>
  );
}
