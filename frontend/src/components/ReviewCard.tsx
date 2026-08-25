import {
  CheckCircle2,
  XCircle,
  TriangleAlert,
  Users,
  MessageCircleOff,
} from "lucide-react";

interface Props {
  report: {
    overall_sentiment: string;
    top_pros: string[];
    top_cons: string[];
    common_complaints: string[];
    best_for: string;
  };
}

export default function ReviewCard({ report }: Props) {
  const hasReviewData =
    report.overall_sentiment.toLowerCase() !== "not available" ||
    report.top_pros.length > 0 ||
    report.top_cons.length > 0 ||
    report.common_complaints.length > 0;

  const sentiment = report.overall_sentiment.toLowerCase();

  const sentimentColor =
    sentiment === "positive"
      ? "bg-green-500/20 text-green-400 border-green-500/30"
      : sentiment === "neutral"
      ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
      : sentiment === "negative"
      ? "bg-red-500/20 text-red-400 border-red-500/30"
      : "bg-slate-500/20 text-gray-400 border-slate-500/30";

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-8 shadow-2xl backdrop-blur-xl">

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">

        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-gray-500">
            Customer Reviews
          </p>

          <h2 className="mt-2 text-3xl font-bold">
            What Customers Say
          </h2>
        </div>

        <span
          className={`rounded-full border px-5 py-2 text-sm font-semibold ${sentimentColor}`}
        >
          {report.overall_sentiment}
        </span>

      </div>

      {/* No review data */}
      {!hasReviewData ? (

        <div className="mt-10 rounded-3xl border border-slate-700 bg-slate-800/40 p-10 text-center">

          <MessageCircleOff
            size={40}
            className="mx-auto text-gray-500"
          />

          <h3 className="mt-5 text-xl font-semibold text-gray-300">
            Review Analysis Unavailable
          </h3>

          <p className="mx-auto mt-3 max-w-2xl leading-7 text-gray-500">
            Customer review data could not be retrieved from this
            product listing. ShopWise-AI will provide sentiment,
            pros, cons, and complaint analysis when review data
            becomes available.
          </p>

        </div>

      ) : (

        <>
          {/* Review insights */}
          <div className="mt-10 grid gap-6 lg:grid-cols-3">

            {/* Pros */}
            <div className="rounded-3xl border border-green-500/20 bg-green-500/5 p-6 transition duration-300 hover:border-green-400/40">

              <div className="flex items-center gap-3">

                <CheckCircle2
                  size={24}
                  className="text-green-400"
                />

                <h3 className="text-xl font-bold text-green-400">
                  Top Pros
                </h3>

              </div>

              <div className="mt-6 space-y-3">

                {report.top_pros.length > 0 ? (
                  report.top_pros.map((pro, index) => (
                    <div
                      key={index}
                      className="rounded-2xl bg-slate-800/70 p-4 text-gray-300"
                    >
                      {pro}
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500">
                    No positive review insights available.
                  </p>
                )}

              </div>

            </div>

            {/* Cons */}
            <div className="rounded-3xl border border-red-500/20 bg-red-500/5 p-6 transition duration-300 hover:border-red-400/40">

              <div className="flex items-center gap-3">

                <XCircle
                  size={24}
                  className="text-red-400"
                />

                <h3 className="text-xl font-bold text-red-400">
                  Top Cons
                </h3>

              </div>

              <div className="mt-6 space-y-3">

                {report.top_cons.length > 0 ? (
                  report.top_cons.map((con, index) => (
                    <div
                      key={index}
                      className="rounded-2xl bg-slate-800/70 p-4 text-gray-300"
                    >
                      {con}
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500">
                    No negative review insights available.
                  </p>
                )}

              </div>

            </div>

            {/* Complaints */}
            <div className="rounded-3xl border border-yellow-500/20 bg-yellow-500/5 p-6 transition duration-300 hover:border-yellow-400/40">

              <div className="flex items-center gap-3">

                <TriangleAlert
                  size={24}
                  className="text-yellow-400"
                />

                <h3 className="text-xl font-bold text-yellow-400">
                  Common Complaints
                </h3>

              </div>

              <div className="mt-6 space-y-3">

                {report.common_complaints.length > 0 ? (
                  report.common_complaints.map(
                    (complaint, index) => (
                      <div
                        key={index}
                        className="rounded-2xl bg-slate-800/70 p-4 text-gray-300"
                      >
                        {complaint}
                      </div>
                    )
                  )
                ) : (
                  <p className="text-gray-500">
                    No common complaints available.
                  </p>
                )}

              </div>

            </div>

          </div>

          {/* Best for */}
          <div className="mt-10 rounded-3xl border border-blue-500/20 bg-blue-500/5 p-6">

            <div className="flex items-center gap-3">

              <Users
                size={24}
                className="text-blue-400"
              />

              <h3 className="text-xl font-bold text-blue-400">
                Best Suitable For
              </h3>

            </div>

            <p className="mt-5 leading-8 text-gray-300">
              {report.best_for}
            </p>

          </div>
        </>

      )}

    </section>
  );
}