import Link from "next/link";
import { Card } from "@/components/ui/Card";

const PIPELINE_STEPS = [
  { icon: "⬆️", label: "Upload" },
  { icon: "📄", label: "Parse" },
  { icon: "🧠", label: "Embed" },
  { icon: "🔍", label: "Match" },
  { icon: "⚖️", label: "Rank" },
  { icon: "✨", label: "Explain" },
];

export default function LandingPage() {
  return (
    <div className="page-container space-y-16">
      {/* Hero */}
      <section className="text-center space-y-4 pt-10">
        <div className="inline-flex items-center gap-2 rounded-full bg-primary-100 px-4 py-1.5 text-sm font-medium text-primary-700">
          <span className="h-2 w-2 rounded-full bg-primary-500 animate-pulse" />
          Powered by Vertex AI + Gemini
        </div>
        <h1 className="text-5xl font-extrabold text-neutral-900 tracking-tight">
          Hire smarter with{" "}
          <span className="text-primary-600">AI screening</span>
        </h1>
        <p className="mx-auto max-w-2xl text-lg text-neutral-500">
          Upload a job description and candidate resumes. Our pipeline uses
          semantic matching, weighted scoring, and Gemini explanations to surface
          the best fit — in seconds.
        </p>
      </section>

      {/* CTA cards */}
      <section className="grid gap-6 sm:grid-cols-2 max-w-2xl mx-auto">
        <Link href="/recruiter" className="group block">
          <Card hover className="h-full flex flex-col items-center text-center gap-4 py-8">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-100 text-2xl group-hover:bg-primary-200 transition-colors">
              🧑‍💼
            </div>
            <div>
              <p className="text-lg font-bold text-neutral-800">I&apos;m a Recruiter</p>
              <p className="mt-1 text-sm text-neutral-500">
                Upload a job description and review ranked candidates
              </p>
            </div>
            <span className="mt-auto inline-flex items-center gap-1 text-sm font-medium text-primary-600">
              Get started
              <svg className="h-4 w-4 group-hover:translate-x-1 transition-transform" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </span>
          </Card>
        </Link>

        <Link href="/candidate" className="group block">
          <Card hover className="h-full flex flex-col items-center text-center gap-4 py-8">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-success-100 text-2xl group-hover:bg-success-200 transition-colors">
              🙋
            </div>
            <div>
              <p className="text-lg font-bold text-neutral-800">I&apos;m a Candidate</p>
              <p className="mt-1 text-sm text-neutral-500">
                Upload your resume and get matched against open roles
              </p>
            </div>
            <span className="mt-auto inline-flex items-center gap-1 text-sm font-medium text-success-600">
              Submit resume
              <svg className="h-4 w-4 group-hover:translate-x-1 transition-transform" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </span>
          </Card>
        </Link>
      </section>

      {/* Pipeline illustration */}
      <section className="space-y-4">
        <h2 className="text-center text-sm font-semibold uppercase tracking-widest text-neutral-400">
          How it works
        </h2>
        <div className="flex flex-wrap items-center justify-center gap-3">
          {PIPELINE_STEPS.map((step, idx) => (
            <div key={step.label} className="flex items-center gap-3">
              <div className="flex flex-col items-center gap-1.5">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white border border-neutral-200 shadow-sm text-xl">
                  {step.icon}
                </div>
                <span className="text-xs font-medium text-neutral-500">{step.label}</span>
              </div>
              {idx < PIPELINE_STEPS.length - 1 && (
                <svg className="h-4 w-4 text-neutral-300 mb-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                </svg>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
