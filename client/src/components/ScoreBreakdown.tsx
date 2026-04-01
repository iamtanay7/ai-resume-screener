import type { ScoreBreakdown as ScoreBreakdownType } from "@/lib/types";
import { ScoreBar } from "@/components/ui/ScoreBar";

interface ScoreBreakdownProps {
  scoreBreakdown: ScoreBreakdownType;
}

const dimensions: {
  key: keyof Omit<ScoreBreakdownType, "overall">;
  label: string;
  weight: number;
  colorClass: string;
}[] = [
  { key: "skills",     label: "Skills Match",          weight: 40, colorClass: "bg-primary-500" },
  { key: "experience", label: "Experience Match",       weight: 30, colorClass: "bg-primary-400" },
  { key: "education",  label: "Education Match",        weight: 15, colorClass: "bg-primary-300" },
  { key: "keywords",   label: "Keywords & Certs",       weight: 15, colorClass: "bg-primary-200" },
];

export function ScoreBreakdown({ scoreBreakdown }: ScoreBreakdownProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wider text-neutral-500">
          Score Breakdown
        </p>
        <span className="text-lg font-bold text-primary-700">
          {scoreBreakdown.overall}
          <span className="text-sm font-normal text-neutral-400">/100</span>
        </span>
      </div>

      <div className="space-y-2.5">
        {dimensions.map(({ key, label, weight, colorClass }) => (
          <ScoreBar
            key={key}
            label={label}
            score={scoreBreakdown[key]}
            weight={weight}
            colorClass={colorClass}
          />
        ))}
      </div>
    </div>
  );
}
