"use client";

import { useState } from "react";
import { Search, Sparkles, Smartphone, Laptop } from "lucide-react";

interface Props {
  onAnalyze: (url: string) => void;
  loading: boolean;
}

export default function SearchBar({ onAnalyze, loading }: Props) {
  const [url, setUrl] = useState("");

  const handleSubmit = () => {
    if (!url.trim() || loading) return;
    onAnalyze(url);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSubmit();
    }
  };

  return (
    <section className="mx-auto max-w-7xl px-6 pt-12 pb-8">

      <div className="text-center">

        <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-5 py-2">

          <Sparkles
            size={16}
            className="text-blue-400"
          />

          <span className="text-sm font-medium text-blue-400">
            AI Powered Shopping Assistant
          </span>

        </div>

        <h1 className="mt-6 text-5xl font-extrabold tracking-tight lg:text-6xl">

          ShopWise

          <span className="text-blue-500">
            AI
          </span>

        </h1>

        <p className="mt-5 text-xl text-gray-400">
          Make smarter buying decisions with AI.
        </p>

        <p className="mx-auto mt-4 max-w-3xl leading-8 text-gray-500">
          Analyze Amazon products using AI-generated insights,
          review intelligence, price analysis and smarter alternatives
          before making your purchase.
        </p>

      </div>

      <div className="mx-auto mt-10 flex max-w-5xl items-center rounded-3xl border border-slate-700 bg-slate-900/70 p-3 backdrop-blur-xl shadow-2xl">

        <Search
          className="ml-4 text-gray-500"
          size={22}
        />

        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Paste Amazon product URL..."
          className="min-w-0 flex-1 bg-transparent px-5 py-4 text-lg outline-none placeholder:text-gray-500"
        />

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="rounded-2xl bg-blue-600 px-8 py-4 font-semibold transition hover:bg-blue-700 disabled:opacity-60"
        >
          {loading ? "Analyzing..." : "Analyze"}
        </button>

      </div>

      <div className="mt-5 flex justify-center">

        <div className="inline-flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900/60 px-4 py-1.5 text-xs text-gray-500">

          <Smartphone size={13} />
          <Laptop size={13} />

          <span>
            ShopWise V1 currently supports Smartphones &amp; Laptops on Amazon
          </span>

        </div>

      </div>

    </section>
  );
}