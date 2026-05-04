"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";

import ChildModeShell from "@/components/child/ChildModeShell";

const cycle = [
  { text: "Breathe in...", seconds: 4, scale: 1.28 },
  { text: "Hold...", seconds: 2, scale: 1.28 },
  { text: "Breathe out...", seconds: 4, scale: 0.82 }
];

export default function ChildBreathingPage() {
  const router = useRouter();
  const [index, setIndex] = useState(0);
  const current = cycle[index];

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setIndex((value) => (value + 1) % cycle.length);
    }, current.seconds * 1000);
    return () => window.clearTimeout(timeout);
  }, [current.seconds]);

  return (
    <ChildModeShell>
      <section className="flex min-h-[62vh] flex-col items-center justify-center gap-10 text-center">
        <motion.div
          animate={{ scale: current.scale }}
          transition={{ duration: current.seconds, ease: "easeInOut" }}
          className="flex h-56 w-56 items-center justify-center rounded-full bg-skysoft shadow-soft"
        >
          <div className="h-32 w-32 rounded-full bg-lavender" />
        </motion.div>
        <h1 className="text-5xl font-bold">{current.text}</h1>
        <button
          type="button"
          onClick={() => router.push("/child")}
          className="min-h-16 rounded-[2rem] bg-ink px-8 py-4 text-2xl font-bold text-white"
        >
          Done
        </button>
      </section>
    </ChildModeShell>
  );
}
