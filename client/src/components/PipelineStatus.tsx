import React from "react";
import type { PipelineStage, PipelineStageStatus } from "@/lib/types";

interface PipelineStatusProps {
  stages: PipelineStage[];
}

const stageConfig: Record<
  PipelineStageStatus,
  { icon: React.ReactNode; ringClass: string; textClass: string }
> = {
  done: {
    icon: (
      <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
      </svg>
    ),
    ringClass: "bg-success-500 text-white",
    textClass: "text-success-700 font-medium",
  },
  processing: {
    icon: (
      <svg className="h-4 w-4 animate-spin-slow" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
      </svg>
    ),
    ringClass: "bg-primary-500 text-white",
    textClass: "text-primary-700 font-medium",
  },
  pending: {
    icon: <span className="h-2 w-2 rounded-full bg-neutral-400" />,
    ringClass: "bg-neutral-200 text-neutral-500",
    textClass: "text-neutral-400",
  },
  error: {
    icon: (
      <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
      </svg>
    ),
    ringClass: "bg-danger-500 text-white",
    textClass: "text-danger-700 font-medium",
  },
};

export function PipelineStatus({ stages }: PipelineStatusProps) {
  return (
    <div className="rounded-xl border border-neutral-200 bg-neutral-50 p-4">
      <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-neutral-500">
        Processing Pipeline
      </p>
      <ol className="flex flex-wrap items-center gap-x-2 gap-y-3">
        {stages.map((stage, idx) => {
          const { icon, ringClass, textClass } = stageConfig[stage.status];
          const isLast = idx === stages.length - 1;
          return (
            <li key={stage.label} className="flex items-center gap-2">
              <div
                className={`flex h-6 w-6 items-center justify-center rounded-full text-xs ${ringClass}`}
              >
                {icon}
              </div>
              <span className={`text-sm ${textClass}`}>{stage.label}</span>
              {!isLast && (
                <svg
                  className="h-3 w-3 text-neutral-300"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                </svg>
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
