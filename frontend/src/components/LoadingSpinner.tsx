"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { BrainCircuit, Loader2 } from "lucide-react";

/*
 * These describe ongoing, generic pipeline activity — never a
 * specific backend stage "completed" state, since the frontend
 * has no way to know real stage progress (no streaming/polling).
 * They exist purely to keep the wait feeling alive, not to report
 * real status.
 */
const STATUS_MESSAGES = [
  "Reading product details from Amazon...",
  "Scanning customer reviews...",
  "Running AI evaluation...",
  "Comparing pricing and value...",
  "Putting together your report...",
];

const MESSAGE_INTERVAL_MS = 4500;
const LONG_WAIT_THRESHOLD_S = 25;

export default function LoadingSpinner() {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    const tick = setInterval(() => {
      setElapsedSeconds((s) => s + 1);
    }, 1000);

    const rotate = setInterval(() => {
      setMessageIndex((i) => (i + 1) % STATUS_MESSAGES.length);
    }, MESSAGE_INTERVAL_MS);

    return () => {
      clearInterval(tick);
      clearInterval(rotate);
    };
  }, []);

  return (
    <div className="mx-auto max-w-2xl px-6">

      <div className="flex flex-col items-center rounded-3xl border border-slate-800 bg-slate-900/70 p-10 text-center shadow-2xl backdrop-blur-xl sm:p-14">

        {/* ==================================================
            SCANNING ICON
        =================================================== */}

        <div className="relative flex h-24 w-24 items-center justify-center">

          <motion.div
            className="absolute inset-0 rounded-full"
            style={{
              background:
                "conic-gradient(from 0deg, transparent, #3b82f6, transparent 40%)",
            }}
            animate={{ rotate: 360 }}
            transition={{ duration: 2.2, repeat: Infinity, ease: "linear" }}
          />

          <div className="absolute inset-[6px] rounded-full bg-slate-900" />

          <motion.div
            animate={{ scale: [1, 1.08, 1] }}
            transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
            className="relative flex h-14 w-14 items-center justify-center rounded-full bg-blue-500/10"
          >
            <BrainCircuit size={26} className="text-blue-400" />
          </motion.div>

        </div>

        {/* ==================================================
            HEADLINE
        =================================================== */}

        <h2 className="mt-7 text-2xl font-bold text-white">
          Analyzing your product
        </h2>

        <div className="mt-3 flex min-h-[1.75rem] items-center gap-2 text-gray-400">
          <Loader2 size={15} className="animate-spin text-blue-400" />
          <motion.span
            key={messageIndex}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            {STATUS_MESSAGES[messageIndex]}
          </motion.span>
        </div>

        {/* ==================================================
            INDETERMINATE ACTIVITY BAR
            (motion only — never tied to a real percentage)
        =================================================== */}

        <div className="mt-8 h-1.5 w-full max-w-sm overflow-hidden rounded-full bg-slate-800">
          <motion.div
            className="h-full w-1/3 rounded-full bg-blue-500"
            animate={{ x: ["-100%", "220%"] }}
            transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
          />
        </div>

        {/* ==================================================
            ELAPSED TIME
        =================================================== */}

        <p className="mt-6 text-sm text-gray-500">
          {elapsedSeconds}s elapsed
        </p>

        {elapsedSeconds >= LONG_WAIT_THRESHOLD_S && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6 }}
            className="mt-3 max-w-sm text-sm text-gray-500"
          >
            Complex products can take a little longer — we&apos;re still working on it.
          </motion.p>
        )}

      </div>

    </div>
  );
}
