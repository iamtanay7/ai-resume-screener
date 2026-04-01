import type { CandidateStatus } from "@/lib/types";

interface StatusBadgeProps {
  status: CandidateStatus;
}

const config: Record<
  CandidateStatus,
  { label: string; classes: string; dot: string }
> = {
  shortlist: {
    label: "Shortlisted",
    classes: "bg-success-100 text-success-800 border-success-200",
    dot: "bg-success-500",
  },
  manual_review: {
    label: "Manual Review",
    classes: "bg-warning-100 text-warning-800 border-warning-200",
    dot: "bg-warning-500",
  },
  reject: {
    label: "Rejected",
    classes: "bg-danger-100 text-danger-800 border-danger-200",
    dot: "bg-danger-500",
  },
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const { label, classes, dot } = config[status];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${classes}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />
      {label}
    </span>
  );
}
