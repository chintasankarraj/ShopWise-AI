interface Props {
  analysis: {
    score: number;
    recommendation: string;
  };
}

/*
 * A fast, at-a-glance verdict. The detailed "why" behind this
 * score (analysis.reasons) is intentionally shown once, in
 * RecommendationCard's "Why?" section further down the page —
 * not duplicated here.
 */
export default function QuickVerdict({ analysis }: Props) {
  const badgeColor =
    analysis.recommendation === "BUY"
      ? "bg-green-500/20 text-green-400 border-green-500/30"
      : analysis.recommendation === "CONSIDER"
      ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
      : "bg-red-500/20 text-red-400 border-red-500/30";

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/70 backdrop-blur-xl p-6 shadow-xl">

      <div className="flex flex-col items-center text-center">

        <span
          className={`inline-flex rounded-full border px-6 py-2 text-sm font-semibold ${badgeColor}`}
        >
          {analysis.recommendation}
        </span>

        <h2 className="mt-5 text-5xl font-bold text-blue-400">
          {analysis.score}
          <span className="text-2xl text-gray-400"> /100</span>
        </h2>

        <p className="mt-2 text-gray-400">
          Overall AI Score
        </p>

      </div>

    </section>
  );
}