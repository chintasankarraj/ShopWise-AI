import Image from "next/image";
import {
  Star,
  Building2,
  IndianRupee,
  ShieldCheck,
} from "lucide-react";

interface Props {
  product: {
    title: string;
    brand: string | null;
    price: string | null;
    rating: number | null;
    reviews: number | null;
    image: string | null;
    availability?: string | null;
    specifications: {
      name: string;
      value: string;
    }[];
  };
}

/**
 * Extract a clean product name from an Amazon-style title.
 *
 * Example:
 *
 * REDMI Note 17 5G (Arctic Blue, 6GB RAM, 128GB ROM) |
 * 8000mAh Battery + 45W Fast Charging | ...
 *
 * becomes:
 *
 * REDMI Note 17 5G
 */
function getCleanProductTitle(title: string): string {
  if (!title) {
    return "Unknown Product";
  }

  // Remove everything after the first pipe.
  let cleanTitle = title.split("|")[0].trim();

  // Remove Amazon marketplace suffixes if present.
  cleanTitle = cleanTitle
    .replace(/\s*:\s*Amazon\.in.*$/i, "")
    .replace(/\s*:\s*Amazon.*$/i, "")
    .trim();

  // Remove configuration inside parentheses.
  cleanTitle = cleanTitle
    .replace(/\s*\([^)]*\)\s*$/, "")
    .trim();

  return cleanTitle || title;
}

/**
 * Extract useful configuration information from the first
 * parenthesized section of the Amazon title.
 *
 * Example:
 *
 * REDMI Note 17 5G (Arctic Blue, 6GB RAM, 128GB ROM)
 *
 * becomes:
 *
 * Arctic Blue · 6GB RAM · 128GB ROM
 */
function getProductConfiguration(title: string): string | null {
  if (!title) {
    return null;
  }

  const match = title.match(/\(([^)]+)\)/);

  if (!match) {
    return null;
  }

  const configuration = match[1]
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
    .join(" · ");

  return configuration || null;
}

export default function ProductCard({ product }: Props) {
  const cleanTitle = getCleanProductTitle(product.title);

  const configuration = getProductConfiguration(
    product.title
  );

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-8 shadow-2xl backdrop-blur-xl">

      {/* Section Heading */}

      <p className="text-sm uppercase tracking-[0.2em] text-gray-500">
        Product Overview
      </p>

      <div className="mt-8 grid gap-10 lg:grid-cols-[360px_1fr]">

        {/* =====================================================
            PRODUCT IMAGE
        ====================================================== */}

        <div>
          <div className="overflow-hidden rounded-3xl border border-slate-700 bg-slate-800">

            {product.image ? (
              <Image
                src={product.image}
                alt={cleanTitle}
                width={500}
                height={500}
                className="h-[360px] w-full object-contain p-8 transition duration-500 hover:scale-105"
              />
            ) : (
              <div className="flex h-[360px] items-center justify-center text-gray-500">
                No Image Available
              </div>
            )}

          </div>
        </div>

        {/* =====================================================
            PRODUCT DETAILS
        ====================================================== */}

        <div className="flex flex-col justify-between">

          <div>

            {/* Brand */}

            <span className="inline-flex items-center rounded-full border border-blue-500/20 bg-blue-500/10 px-5 py-2 text-sm font-semibold text-blue-400">
              {product.brand || "Unknown Brand"}
            </span>

            {/* Clean Product Title */}

            <h2 className="mt-6 text-4xl font-bold leading-tight tracking-tight">
              {cleanTitle}
            </h2>

            {/* Product Configuration */}

            {configuration && (
              <p className="mt-4 text-lg font-medium text-gray-400">
                {configuration}
              </p>
            )}

            {/* Availability */}

            <div className="mt-5 flex items-center gap-3">

              <ShieldCheck
                size={18}
                className="text-green-400"
              />

              <span className="text-sm text-gray-400">
                {product.availability || "Availability Unknown"}
              </span>

            </div>

          </div>

          {/* =====================================================
              PRODUCT STATS
          ====================================================== */}

          <div className="mt-10 grid gap-5 md:grid-cols-3">

            {/* =================================================
                PRICE
            ================================================== */}

            <div className="rounded-3xl border border-slate-700 bg-slate-800/70 p-6 transition-all duration-300 hover:-translate-y-1 hover:border-green-400/40">

              <IndianRupee
                className="mb-4 text-green-400"
                size={26}
              />

              <p className="text-sm text-gray-400">
                Price
              </p>

              <h3 className="mt-2 break-words text-3xl font-extrabold text-green-400">
                {product.price || "N/A"}
              </h3>

            </div>

            {/* =================================================
                RATING
            ================================================== */}

            <div className="rounded-3xl border border-slate-700 bg-slate-800/70 p-6 transition-all duration-300 hover:-translate-y-1 hover:border-yellow-400/40">

              <Star
                size={26}
                className="mb-4 fill-yellow-400 text-yellow-400"
              />

              <p className="text-sm text-gray-400">
                Rating
              </p>

              <h3 className="mt-2 text-3xl font-bold">
                {product.rating ?? "N/A"}
              </h3>

            </div>

            {/* =================================================
                REVIEWS
            ================================================== */}

            <div className="rounded-3xl border border-slate-700 bg-slate-800/70 p-6 transition-all duration-300 hover:-translate-y-1 hover:border-blue-400/40">

              <Building2
                size={26}
                className="mb-4 text-blue-400"
              />

              <p className="text-sm text-gray-400">
                Reviews
              </p>

              <h3 className="mt-2 text-3xl font-bold">
                {product.reviews ?? "N/A"}
              </h3>

            </div>

          </div>

        </div>

      </div>

    </section>
  );
}