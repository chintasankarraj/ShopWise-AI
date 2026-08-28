import CountUp from "react-countup";
import {
  CircularProgressbar,
  buildStyles,
} from "react-circular-progressbar";

import "react-circular-progressbar/dist/styles.css";

interface Props {
  analysis: {
    score: number;
    recommendation: string;
    reasons: string[];
    summary: string;
  };
}

export default function RecommendationCard({ analysis }: Props) {
  const badgeColor =
    analysis.recommendation === "BUY"
      ? "bg-green-500/20 text-green-400 border-green-500/30"
      : analysis.recommendation === "CONSIDER"
      ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
      : "bg-red-500/20 text-red-400 border-red-500/30";

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-8 backdrop-blur-xl shadow-2xl">

      <p className="text-sm uppercase tracking-[0.2em] text-gray-500">
        AI Recommendation
      </p>

      <div className="mt-10 flex flex-col items-center">

        <div className="relative h-56 w-56">

          <CircularProgressbar
            value={analysis.score}
            styles={buildStyles({
              pathColor: "#3b82f6",
              trailColor: "#1e293b",
            })}
          />

          <div className="absolute inset-0 flex flex-col items-center justify-center">

            <h2 className="text-5xl font-bold text-white">

              <CountUp
                end={analysis.score}
                duration={2}
              />

            </h2>

            <p className="text-sm text-gray-400">
              /100
            </p>

          </div>

        </div>

        <p className="mt-4 uppercase tracking-[0.2em] text-gray-400 text-sm">
          AI Buying Score
        </p>

        <span
          className={`mt-6 rounded-full border px-6 py-2 text-sm font-semibold shadow-lg ${badgeColor}`}
        >
          {analysis.recommendation}
        </span>

      </div>

      <hr className="my-10 border-slate-700" />

      <div>

        <h3 className="text-xl font-bold">
          Why?
        </h3>

        <div className="mt-5 flex flex-wrap gap-3">

          {analysis.reasons.map((reason) => (

            <span
              key={reason}
              className="rounded-full border border-blue-500/20 bg-blue-500/10 px-4 py-2 text-blue-300 transition hover:bg-blue-500/20"
            >
              {reason}
            </span>

          ))}

        </div>

      </div>

      <div className="mt-10 rounded-3xl border border-slate-700 bg-slate-800/60 p-6">

        <h3 className="text-xl font-bold">
          Score Summary
        </h3>

        <p className="mt-5 leading-8 text-gray-300">
          {analysis.summary}
        </p>

      </div>

    </section>
  );
}