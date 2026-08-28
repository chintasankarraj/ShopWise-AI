const SECTIONS = [
  { id: "section-overview", label: "Overview" },
  { id: "section-score", label: "Score" },
  { id: "section-specs", label: "Specs" },
  { id: "section-breakdown", label: "Why" },
  { id: "section-reviews", label: "Reviews" },
  { id: "section-ai", label: "AI Insights" },
  { id: "section-alternatives", label: "Alternatives" },
];

/*
 * A lightweight, always-visible way to jump between sections of
 * a long results page — anchor links only, no scroll-spy/active
 * tracking, kept intentionally simple.
 */
export default function ResultsNav() {
  return (
    <nav className="sticky top-0 z-30 border-b border-slate-800 bg-slate-950/90 backdrop-blur-xl">

      <div className="mx-auto flex max-w-7xl gap-2 overflow-x-auto px-6 py-3">

        {SECTIONS.map((section) => (
          <a
            key={section.id}
            href={`#${section.id}`}
            className="shrink-0 whitespace-nowrap rounded-full border border-slate-700 bg-slate-800/60 px-4 py-1.5 text-sm text-gray-300 transition hover:border-blue-500/40 hover:bg-slate-800 hover:text-white"
          >
            {section.label}
          </a>
        ))}

      </div>

    </nav>
  );
}
