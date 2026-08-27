import {
  ArrowRight,
  BadgeIndianRupee,
  ExternalLink,
  Sparkles,
} from "lucide-react";

interface Alternative {
  name: string;
  price: string;
  reason: string;
  url: string;
  availability?: string;
  verified?: boolean;
}

interface Props {
  alternatives: Alternative[];
}

export default function AlternativesCard({
  alternatives,
}: Props) {
  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-8 shadow-2xl backdrop-blur-xl">

      {/* Header */}
      <div className="flex items-center gap-3">

        <Sparkles
          size={22}
          className="text-blue-400"
        />

        <div>

          <p className="text-sm uppercase tracking-[0.2em] text-gray-500">
            AI Suggestions
          </p>

          <h2 className="mt-2 text-3xl font-bold">
            Better Alternatives
          </h2>

        </div>

      </div>

      {/* Description */}
      <p className="mt-4 max-w-3xl leading-7 text-gray-400">
        Discover currently available alternatives that may offer
        better performance, features, or value for money.
      </p>

      {/* No alternatives */}
      {alternatives.length === 0 ? (

        <div className="mt-10 rounded-2xl border border-slate-700 bg-slate-800/40 p-8 text-center">

          <Sparkles
            size={32}
            className="mx-auto text-gray-500"
          />

          <h3 className="mt-4 text-xl font-semibold text-gray-300">
            No Current Alternatives Found
          </h3>

          <p className="mx-auto mt-3 max-w-xl leading-7 text-gray-500">
            ShopWise-AI could not verify enough currently available
            alternatives for this product.
          </p>

        </div>

      ) : (

        /* Alternatives */
        <div className="mt-10 grid gap-6 lg:grid-cols-3">

          {alternatives.map((item, index) => (

            <div
              key={`${item.name}-${index}`}
              className="group flex flex-col rounded-3xl border border-slate-700 bg-slate-800/60 p-6 transition-all duration-300 hover:-translate-y-2 hover:border-blue-500/40 hover:shadow-xl"
            >

              {/* Rank + Price */}
              <div className="flex items-center justify-between gap-4">

                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-blue-500/10 font-bold text-blue-400">
                  #{index + 1}
                </span>

                <div className="flex items-center gap-2 text-green-400">

                  <BadgeIndianRupee size={18} />

                  <span className="font-semibold text-right">
                    {item.price || "Price unavailable"}
                  </span>

                </div>

              </div>

              {/* Availability -- only a confirmed listing gets the
                  green "available" styling; anything we couldn't
                  verify is shown with a neutral, honest badge
                  instead of implying it's in stock. */}
              {item.availability && (
                <div className="mt-5">

                  <span
                    className={
                      item.verified
                        ? "inline-flex rounded-full border border-green-500/20 bg-green-500/10 px-3 py-1 text-xs font-medium text-green-400"
                        : "inline-flex rounded-full border border-slate-600/40 bg-slate-700/30 px-3 py-1 text-xs font-medium text-gray-400"
                    }
                  >
                    {item.availability}
                  </span>

                </div>
              )}

              {/* Product Name */}
              <h3 className="mt-6 text-2xl font-bold leading-8 transition-colors group-hover:text-blue-400">
                {item.name}
              </h3>

              {/* Reason */}
              <p className="mt-5 flex-1 leading-7 text-gray-400">
                {item.reason}
              </p>

              {/* Button */}
              {item.url ? (

                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-8 flex w-full items-center justify-center gap-2 rounded-2xl bg-blue-600 py-3 font-semibold transition-all duration-300 hover:bg-blue-700 hover:shadow-lg"
                >

                  View Alternative

                  <ArrowRight size={18} />

                  <ExternalLink
                    size={15}
                    className="opacity-70"
                  />

                </a>

              ) : (

                <button
                  type="button"
                  disabled
                  className="mt-8 flex w-full cursor-not-allowed items-center justify-center gap-2 rounded-2xl bg-slate-700 py-3 font-semibold text-gray-500"
                >

                  Link Unavailable

                  <ExternalLink size={17} />

                </button>

              )}

            </div>

          ))}

        </div>

      )}

    </section>
  );
}