"use client";

import { useState } from "react";

import SearchBar from "./SearchBar";
import LoadingSpinner from "./LoadingSpinner";
import ErrorCard from "./ErrorCard";
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

      setError("Failed to analyze the product. Please try again.");

      toast.error("Analysis failed.");
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

      {loading && (
        <div className="mx-auto mt-16 flex max-w-7xl justify-center px-6">
          <LoadingSpinner />
        </div>
      )}

      {error && (
        <div className="mx-auto mt-10 max-w-7xl px-6">
          <ErrorCard message={error} />
        </div>
      )}

      {result && (
        <main className="mx-auto mt-10 max-w-7xl space-y-8 px-6 pb-24">

          <QuickVerdict
            analysis={result.analysis}
          />

          <ProductCard
            product={result.product}
          />

          <section className="grid items-start gap-8 lg:grid-cols-2">

            <RecommendationCard
              analysis={result.analysis}
            />

            <SpecsCard
              specifications={result.product.specifications ?? []}
            />

          </section>

          <section className="grid items-start gap-8 lg:grid-cols-2">

            <ReviewCard
              report={result.review_report}
            />

            <PriceCard
              report={result.price_report}
            />

          </section>

          <AIReportCard
            report={result.ai_report}
          />

          <AlternativesCard
            alternatives={result.alternatives}
          />

        </main>
      )}
    </>
  );
}