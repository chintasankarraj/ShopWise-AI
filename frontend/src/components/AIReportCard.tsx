import {
  BrainCircuit,
  ShieldCheck,
  CircleX,
  Sparkles,
  Cpu,
  Battery,
  Monitor,
  Camera,
  IndianRupee,
  Shield,
} from "lucide-react";

interface CategoryScore {
  score: number;
  reason?: string;
}

interface Props {
  report: {
    overall_score: number;
    recommendation: string;
    summary: string;
    pros: string[];
    cons: string[];

    category_scores?: {
      performance?: CategoryScore;
      battery?: CategoryScore;
      display?: CategoryScore;
      camera?: CategoryScore;
      value?: CategoryScore;
      durability?: CategoryScore;
    };
  };
}

export default function AIReportCard({
  report,
}: Props) {

  const recommendation =
    report.recommendation.toUpperCase();

  const badgeColor =
    recommendation === "BUY"
      ? "bg-green-500/20 text-green-400 border-green-500/30"
      : recommendation === "CONSIDER"
      ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
      : "bg-red-500/20 text-red-400 border-red-500/30";

  /*
   * Category score configuration
   */

  const categoryScores = [
    {
      key: "performance",
      label: "Performance",
      icon: Cpu,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
      border: "border-blue-500/20",
      data: report.category_scores?.performance,
    },
    {
      key: "battery",
      label: "Battery",
      icon: Battery,
      color: "text-green-400",
      bg: "bg-green-500/10",
      border: "border-green-500/20",
      data: report.category_scores?.battery,
    },
    {
      key: "display",
      label: "Display",
      icon: Monitor,
      color: "text-purple-400",
      bg: "bg-purple-500/10",
      border: "border-purple-500/20",
      data: report.category_scores?.display,
    },
    {
      key: "camera",
      label: "Camera",
      icon: Camera,
      color: "text-pink-400",
      bg: "bg-pink-500/10",
      border: "border-pink-500/20",
      data: report.category_scores?.camera,
    },
    {
      key: "value",
      label: "Value",
      icon: IndianRupee,
      color: "text-yellow-400",
      bg: "bg-yellow-500/10",
      border: "border-yellow-500/20",
      data: report.category_scores?.value,
    },
    {
      key: "durability",
      label: "Durability",
      icon: Shield,
      color: "text-cyan-400",
      bg: "bg-cyan-500/10",
      border: "border-cyan-500/20",
      data: report.category_scores?.durability,
    },
  ];

  const hasCategoryScores =
    categoryScores.some(
      (category) =>
        category.data &&
        typeof category.data.score === "number"
    );

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
          CATEGORY SCORE BREAKDOWN
      ====================================================== */}

      {hasCategoryScores && (

        <div className="mt-10">

          <div className="flex items-center gap-3">

            <Sparkles
              size={22}
              className="text-purple-400"
            />

            <div>

              <p className="text-sm uppercase tracking-[0.2em] text-gray-500">
                AI Score Breakdown
              </p>

              <h3 className="mt-1 text-2xl font-bold">
                How the score is built
              </h3>

            </div>

          </div>


          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">

            {categoryScores.map((category) => {

              const Icon = category.icon;

              const score =
                category.data?.score;

              if (
                typeof score !== "number"
              ) {
                return null;
              }

              return (

                <div
                  key={category.key}
                  className={`rounded-3xl border ${category.border} bg-slate-800/60 p-5 transition-all duration-300 hover:-translate-y-1`}
                >

                  <div className="flex items-center justify-between">

                    <div className="flex items-center gap-3">

                      <div
                        className={`flex h-11 w-11 items-center justify-center rounded-2xl ${category.bg}`}
                      >
                        <Icon
                          size={21}
                          className={category.color}
                        />
                      </div>

                      <span className="font-semibold">
                        {category.label}
                      </span>

                    </div>

                    <span
                      className={`text-xl font-bold ${category.color}`}
                    >
                      {score}
                    </span>

                  </div>


                  {/* Progress Bar */}

                  <div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-700">

                    <div
                      className="h-full rounded-full bg-current transition-all duration-700"
                      style={{
                        width: `${Math.min(
                          Math.max(score, 0),
                          100
                        )}%`,
                      }}
                    />

                  </div>


                  {category.data?.reason && (

                    <p className="mt-4 text-sm leading-6 text-gray-400">
                      {category.data.reason}
                    </p>

                  )}

                </div>

              );

            })}

          </div>

        </div>

      )}


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

            {report.pros.length > 0 ? (

              report.pros.map(
                (pro, index) => (

                  <div
                    key={`${pro}-${index}`}
                    className="rounded-2xl bg-slate-800/70 p-4 text-gray-300"
                  >
                    {pro}
                  </div>

                )
              )

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