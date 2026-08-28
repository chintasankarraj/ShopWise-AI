import {
  BrainCircuit,
  ShieldCheck,
  CircleX,
  Sparkles,
} from "lucide-react";

interface Props {
  report: {
    overall_score: number;
    recommendation: string;
    summary: string;
    pros: string[];
    cons: string[];
  };
  /*
   * The score-breakdown reasons already shown in
   * RecommendationCard's "Why?" section. When the backend's
   * AI report falls back to reusing that same list verbatim
   * for "pros" (it does when live AI insights are unavailable),
   * we avoid showing the identical text a second time here.
   */
  reasons?: string[];
}

export default function AIReportCard({
  report,
  reasons = [],
}: Props) {

  const recommendation =
    report.recommendation.toUpperCase();

  const badgeColor =
    recommendation === "BUY"
      ? "bg-green-500/20 text-green-400 border-green-500/30"
      : recommendation === "CONSIDER"
      ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
      : "bg-red-500/20 text-red-400 border-red-500/30";

  const alreadyShownReasons = new Set(
    reasons.map((reason) => reason.trim().toLowerCase())
  );

  const newPros = report.pros.filter(
    (pro) => !alreadyShownReasons.has(pro.trim().toLowerCase())
  );

  const prosFullyDuplicateReasons =
    report.pros.length > 0 && newPros.length === 0;

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-8 shadow-2xl backdrop-blur-xl">

      {/* =====================================================
          HEADER
      ====================================================== */}

      <div className="flex flex-wrap items-center justify-between gap-6">

        <div>

          <div className="flex items-center gap-3">

            <BrainCircuit
              size={24}
              className="text-blue-400"
            />

            <p className="text-sm uppercase tracking-[0.2em] text-gray-500">
              Intelligent Product Analysis
            </p>

          </div>

          <h2 className="mt-6 text-6xl font-extrabold text-blue-400">
            {report.overall_score}

            <span className="text-2xl text-gray-400">
              /100
            </span>
          </h2>

          <p className="mt-3 text-gray-400">
            Overall Product Evaluation
          </p>

        </div>

        <span
          className={`rounded-full border px-8 py-3 text-lg font-bold ${badgeColor}`}
        >
          {recommendation}
        </span>

      </div>


      {/* =====================================================
          METHODOLOGY
      ====================================================== */}

      <div className="mt-10 rounded-2xl border border-blue-500/20 bg-blue-500/5 p-5">

        <div className="flex items-start gap-3">

          <BrainCircuit
            size={22}
            className="mt-1 shrink-0 text-blue-400"
          />

          <div>

            <p className="font-semibold text-blue-400">
              How this score is calculated
            </p>

            <p className="mt-2 text-sm leading-7 text-gray-400">

              ShopWise AI evaluates the product using its
              extracted specifications, category-specific
              scoring rules, price information, and available
              product intelligence.

            </p>

          </div>

        </div>

      </div>


      {/* =====================================================
          EXECUTIVE SUMMARY
      ====================================================== */}

      <div className="mt-10 rounded-3xl border border-slate-700 bg-slate-800/60 p-8">

        <div className="flex items-center gap-3">

          <Sparkles
            size={22}
            className="text-purple-400"
          />

          <h3 className="text-xl font-bold">
            Executive Summary
          </h3>

        </div>

        <p className="mt-5 leading-8 text-gray-300">
          {report.summary}
        </p>

      </div>


      {/* =====================================================
          STRENGTHS & WEAKNESSES
      ====================================================== */}

      <div className="mt-10 grid gap-6 lg:grid-cols-2">


        {/* ---------------------------------------------------
            STRENGTHS
        ---------------------------------------------------- */}

        <div className="rounded-3xl border border-green-500/20 bg-green-500/5 p-6 transition duration-300 hover:border-green-400/40">

          <div className="flex items-center gap-3">

            <ShieldCheck
              size={24}
              className="text-green-400"
            />

            <h3 className="text-xl font-bold text-green-400">
              Key Strengths
            </h3>

          </div>

          <div className="mt-6 space-y-3">

            {newPros.length > 0 ? (

              newPros.map(
                (pro, index) => (

                  <div
                    key={`${pro}-${index}`}
                    className="rounded-2xl bg-slate-800/70 p-4 text-gray-300"
                  >
                    {pro}
                  </div>

                )
              )

            ) : prosFullyDuplicateReasons ? (

              <p className="text-gray-500">
                Already covered in &quot;Why?&quot; above — the AI&apos;s
                strengths match the score reasons.
              </p>

            ) : (

              <p className="text-gray-500">
                No strengths identified.
              </p>

            )}

          </div>

        </div>


        {/* ---------------------------------------------------
            WEAKNESSES
        ---------------------------------------------------- */}

        <div className="rounded-3xl border border-red-500/20 bg-red-500/5 p-6 transition duration-300 hover:border-red-400/40">

          <div className="flex items-center gap-3">

            <CircleX
              size={24}
              className="text-red-400"
            />

            <h3 className="text-xl font-bold text-red-400">
              Key Weaknesses
            </h3>

          </div>

          <div className="mt-6 space-y-3">

            {report.cons.length > 0 ? (

              report.cons.map(
                (con, index) => (

                  <div
                    key={`${con}-${index}`}
                    className="rounded-2xl bg-slate-800/70 p-4 text-gray-300"
                  >
                    {con}
                  </div>

                )
              )

            ) : (

              <p className="text-gray-500">
                No significant weaknesses identified.
              </p>

            )}

          </div>

        </div>

      </div>

    </section>
  );
}