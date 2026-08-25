"use client";

import { useState } from "react";
import { GitCompareArrows } from "lucide-react";

interface Props {
  onCompare: (url1: string, url2: string) => void;
  loading: boolean;
}

export default function CompareSection({
  onCompare,
  loading,
}: Props) {
  const [url1, setUrl1] = useState("");
  const [url2, setUrl2] = useState("");

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-8 backdrop-blur-xl">

      <div className="flex items-center gap-3">

        <GitCompareArrows className="text-blue-400" />

        <h2 className="text-3xl font-bold">
          Compare Products
        </h2>

      </div>

      <p className="mt-2 text-gray-400">
        Compare two Amazon products and let AI decide the better choice.
      </p>

      <div className="mt-8 grid gap-5 lg:grid-cols-2">

        <input
          value={url1}
          onChange={(e) => setUrl1(e.target.value)}
          placeholder="Amazon Product URL 1"
          className="rounded-2xl border border-slate-700 bg-slate-800 p-4 outline-none"
        />

        <input
          value={url2}
          onChange={(e) => setUrl2(e.target.value)}
          placeholder="Amazon Product URL 2"
          className="rounded-2xl border border-slate-700 bg-slate-800 p-4 outline-none"
        />

      </div>

      <button
        disabled={loading}
        onClick={() => onCompare(url1, url2)}
        className="mt-8 rounded-2xl bg-blue-600 px-8 py-4 font-semibold hover:bg-blue-700"
      >
        Compare Products
      </button>

    </section>
  );
}