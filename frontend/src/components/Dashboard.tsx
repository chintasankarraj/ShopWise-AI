"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

import SearchBar from "./SearchBar";
import LoadingSpinner from "./LoadingSpinner";
import ErrorCard from "./ErrorCard";
import ResultsNav from "./ResultsNav";
import QuickVerdict from "./QuickVerdict";
import ProductCard from "./ProductCard";
import RecommendationCard from "./RecommendationCard";
import SpecsCard from "./SpecsCard";
import ReviewCard from "./ReviewCard";
import PriceCard from "./PriceCard";
import AIReportCard from "./AIReportCard";
import AlternativesCard from "./AlternativesCard";

import { toast } from "sonner";

import { analyzeProduct } from "@/services/api";
import { ProductAnalysis } from "@/types/product";

export default function Dashboard() {
  const [result, setResult] = useState<ProductAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleAnalyze(url: string) {
    if (!url.trim()) {
      setError("Please enter a valid Amazon product URL.");
      toast.error("Please enter a valid URL.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await analyzeProduct(url);

      setResult(data);

      toast.success("Analysis completed successfully!");
    } catch (err) {
      console.error(err);

      const message =
        err instanceof Error && err.message
          ? err.message
          : "Failed to analyze the product. Please try again.";

      setError(message);

      toast.error(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <SearchBar
        onAnalyze={handleAnalyze}
        loading={loading}
      />

      {/*
       * Rendered outside AnimatePresence/motion so it never sits
       * inside a transformed ancestor — position: sticky silently
       * stops working when an ancestor has a transform applied.
       */}
      {!loading && result && <ResultsNav />}

      <AnimatePresence mode="wait">

        {loading && (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="mx-auto mt-16 flex max-w-7xl justify-center px-6"
          >
            <LoadingSpinner />
          </motion.div>
        )}

        {!loading && error && (
          <motion.div
            key="error"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="mx-auto mt-10 max-w-7xl px-6"
          >
            <ErrorCard message={error} />
          </motion.div>
        )}

        {!loading && result && (
          <motion.main
            key="result"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35 }}
            className="mx-auto mt-10 max-w-7xl space-y-8 px-6 pb-24"
          >

            {/* 1. Product overview */}
            <div id="section-overview" className="scroll-mt-20">
              <ProductCard
                product={result.product}
              />
            </div>

            {/* 2. Score / verdict */}
            <div id="section-score" className="scroll-mt-20">
              <QuickVerdict
                analysis={result.analysis}
              />
            </div>

            {/* 3. Key specifications */}
            <div id="section-specs" className="scroll-mt-20">
              <SpecsCard
                specifications={result.product.specifications ?? []}
              />
            </div>

            {/* 4. Score breakdown / reasons */}
            <div id="section-breakdown" className="scroll-mt-20">
              <RecommendationCard
                analysis={result.analysis}
              />
            </div>

            {/* 5. Reviews + price */}
            <section id="section-reviews" className="scroll-mt-20 grid items-start gap-8 lg:grid-cols-2">

              <ReviewCard
                report={result.review_report}
              />

              <PriceCard
                report={result.price_report}
              />

            </section>

            {/* 6. AI insights */}
            <div id="section-ai" className="scroll-mt-20">
              <AIReportCard
                report={result.ai_report}
                reasons={result.analysis.reasons}
              />
            </div>

            {/* 7. Alternatives */}
            <div id="section-alternatives" className="scroll-mt-20">
              <AlternativesCard
                alternatives={result.alternatives}
              />
            </div>

          </motion.main>
        )}

      </AnimatePresence>
    </>
  );
}