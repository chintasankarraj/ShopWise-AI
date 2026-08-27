import {
  TrendingDown,
  Wallet,
  Sparkles,
} from "lucide-react";

interface Props {
  report: {
    current_value: string;
    expected_sale_price: string;
    buy_advice: string;
    reason: string;
  };
}

export default function PriceCard({ report }: Props) {
  const advice = report.buy_advice.toUpperCase();

  const badgeColor =
    advice === "BUY"
      ? "bg-green-500/20 text-green-400 border-green-500/30"
      : advice === "WAIT"
      ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
      : advice === "CONSIDER"
      ? "bg-blue-500/20 text-blue-400 border-blue-500/30"
      : "bg-red-500/20 text-red-400 border-red-500/30";

  const recommendationText =
    advice === "BUY"
      ? "The current price appears attractive based on the available product information."
      : advice === "WAIT"
      ? "Waiting for a better price may be worthwhile."
      : advice === "CONSIDER"
      ? "The product specifications look reasonable, but price-history data is not available yet."
      : "The available information does not currently indicate strong value for money.";

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-8 shadow-2xl backdrop-blur-xl">

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">

        <div>

          <p className="text-sm uppercase tracking-[0.2em] text-gray-500">
            Price Intelligence
          </p>

          <h2 className="mt-2 text-3xl font-bold">
            Is This a Good Deal?
          </h2>

        </div>

        <span
          className={`rounded-full border px-6 py-2 text-sm font-semibold ${badgeColor}`}
        >
          {report.buy_advice}
        </span>

      </div>

      {/* Price Information */}
      <div className="mt-10">

        {/* Current Price */}
        <div className="rounded-3xl border border-slate-700 bg-slate-800/60 p-6 transition duration-300 hover:-translate-y-1 hover:border-green-400/30">

          <div className="flex items-center gap-3">

            <Wallet
              size={24}
              className="text-green-400"
            />

            <p className="text-sm uppercase tracking-[0.2em] text-gray-500">
              Current Price
            </p>

          </div>

          <h3 className="mt-5 text-3xl font-bold text-green-400">
            {report.current_value}
          </h3>

        </div>

      </div>

      {/* AI Price Insight */}
      <div className="mt-10 rounded-3xl border border-purple-500/20 bg-purple-500/5 p-6">

        <div className="flex items-center gap-3">

          <Sparkles
            size={24}
            className="text-purple-400"
          />

          <h3 className="text-xl font-bold text-purple-400">
            AI Price Insight
          </h3>

        </div>

        <p className="mt-5 leading-8 text-gray-300">
          {report.reason}
        </p>

      </div>

      {/* Recommendation */}
      <div className="mt-8 flex items-start gap-3 rounded-2xl bg-slate-800/60 p-5">

        <TrendingDown
          size={22}
          className="mt-1 shrink-0 text-cyan-400"
        />

        <p className="leading-7 text-gray-300">

          <span className="font-semibold text-white">
            Recommendation:
          </span>{" "}

          {recommendationText}

        </p>

      </div>

    </section>
  );
}