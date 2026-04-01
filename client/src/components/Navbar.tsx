import Link from "next/link";

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-neutral-200 bg-white/90 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link
          href="/"
          className="flex items-center gap-2 text-lg font-bold text-primary-700 hover:text-primary-800 transition-colors"
        >
          <BrainIcon />
          ResumeAI
        </Link>

        <nav className="flex items-center gap-6 text-sm font-medium text-neutral-600">
          <Link
            href="/recruiter"
            className="hover:text-primary-600 transition-colors"
          >
            Recruiter
          </Link>
          <Link
            href="/candidate"
            className="hover:text-primary-600 transition-colors"
          >
            Candidate
          </Link>
          <Link
            href="/results"
            className="rounded-lg bg-primary-600 px-3 py-1.5 text-white hover:bg-primary-700 transition-colors"
          >
            Results
          </Link>
        </nav>
      </div>
    </header>
  );
}

function BrainIcon() {
  return (
    <svg
      className="h-6 w-6"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.8}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"
      />
    </svg>
  );
}
