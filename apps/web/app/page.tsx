"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, ShieldCheck } from "lucide-react";

export default function HomePage() {
  return (
    <main className="min-h-screen overflow-hidden bg-cream text-ink">
      <section className="mx-auto grid min-h-screen max-w-7xl items-center gap-10 px-6 py-12 md:grid-cols-[1.05fr_0.95fr] md:px-10">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="space-y-8"
        >
          <div className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-semibold shadow-soft">
            <ShieldCheck className="h-4 w-4 text-emerald-700" />
            Parent-guided comfort for tender moments
          </div>
          <div className="space-y-5">
            <h1 className="max-w-4xl text-6xl font-bold leading-[0.95] tracking-normal md:text-8xl">
              Your voice. Their comfort.
            </h1>
            <p className="max-w-2xl text-lg leading-8 text-ink/72 md:text-xl">
              Always Near helps parents create a gentle AI comfort helper for familiar
              routines, reassurance, and moments when a child needs a calm prompt.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/parent/onboarding"
              className="inline-flex items-center gap-2 rounded-full bg-ink px-6 py-4 text-sm font-semibold text-white shadow-soft"
            >
              Create account
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center rounded-full border border-ink/15 bg-white px-6 py-4 text-sm font-semibold text-ink"
            >
              Log in
            </Link>
          </div>
          <p className="max-w-xl rounded-3xl bg-white/70 px-5 py-4 text-sm text-ink/70">
            Always Near is an AI comfort helper, not an emergency service.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="relative min-h-[420px] rounded-[3rem] bg-skysoft p-8 shadow-soft"
        >
          <svg viewBox="0 0 520 520" role="img" aria-label="Soft helper illustration">
            <rect x="46" y="54" width="428" height="412" rx="76" fill="#fff7ed" />
            <circle cx="260" cy="206" r="88" fill="#ebe4ff" />
            <path
              d="M145 356c34-62 70-92 115-92s81 30 115 92"
              fill="none"
              stroke="#253044"
              strokeWidth="18"
              strokeLinecap="round"
            />
            <path
              d="M184 198c22-30 48-45 76-45s54 15 76 45"
              fill="none"
              stroke="#253044"
              strokeWidth="16"
              strokeLinecap="round"
            />
            <circle cx="219" cy="222" r="9" fill="#253044" />
            <circle cx="301" cy="222" r="9" fill="#253044" />
            <path
              d="M223 272c22 18 52 18 74 0"
              fill="none"
              stroke="#253044"
              strokeWidth="12"
              strokeLinecap="round"
            />
            <path
              d="M104 148c-22 36-26 74-12 114"
              fill="none"
              stroke="#a7d8f4"
              strokeWidth="18"
              strokeLinecap="round"
            />
            <path
              d="M416 148c22 36 26 74 12 114"
              fill="none"
              stroke="#a7d8f4"
              strokeWidth="18"
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute bottom-8 left-8 right-8 rounded-[2rem] bg-white/85 p-5">
            <p className="text-sm font-semibold">Mum&apos;s Always Near helper</p>
            <p className="mt-1 text-sm text-ink/65">
              Honest helper identity, parent control, and safety checks from the start.
            </p>
          </div>
        </motion.div>
      </section>
    </main>
  );
}
