"use client";

interface ScoreBarProps {
  label: string;
  score: number;   // 0–100
  weight: number;  // e.g. 40 for 40%
  colorClass?: string;
}

export function ScoreBar({
  label,
  score,
  weight,
  colorClass = "bg-primary-500",
}: ScoreBarProps) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs text-neutral-600">
        <span className="font-medium">{label}</span>
        <span className="flex items-center gap-2">
          <span className="text-neutral-400">weight {weight}%</span>
          <span className="font-semibold text-neutral-800">{score}/100</span>
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-neutral-200">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${colorClass}`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}
