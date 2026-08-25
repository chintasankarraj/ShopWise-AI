interface Props {
  analysis: {
    score: number;
    recommendation: string;
    reasons: string[];
  };
}

export default function QuickVerdict({ analysis }: Props) {
  const badgeColor =
    analysis.recommendation === "BUY"
      ? "bg-green-500/20 text-green-400 border-green-500/30"
      : analysis.recommendation === "CONSIDER"
      ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
      : "bg-red-500/20 text-red-400 border-red-500/30";

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/70 backdrop-blur-xl p-8 shadow-xl">

      <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">

        <div>

          <span
            className={`inline-flex rounded-full border px-5 py-2 text-sm font-semibold ${badgeColor}`}
          >
            {analysis.recommendation}
          </span>

          <h2 className="mt-6 text-5xl font-bold text-blue-400">
            {analysis.score}
            <span className="text-2xl text-gray-400"> /100</span>
          </h2>

          <p className="mt-2 text-gray-400">
            Overall AI Score
          </p>

        </div>

        <div className="flex flex-wrap gap-3">

          {analysis.reasons.map((reason) => (
            <span
              key={reason}
              className="rounded-full border border-blue-500/20 bg-blue-500/10 px-4 py-2 text-sm text-blue-300"
            >
              ✓ {reason}
            </span>
          ))}

        </div>

      </div>

    </section>
  );
}