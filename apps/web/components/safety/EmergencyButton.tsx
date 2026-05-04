"use client";

import { useRouter } from "next/navigation";

export function EmergencyButton({ compact = false }: { compact?: boolean }) {
  const router = useRouter();

  return (
    <button
      type="button"
      onClick={() => router.push("/child/grown-up")}
      className={`fixed left-4 right-4 z-40 rounded-[2rem] bg-emergency font-bold text-white shadow-soft transition active:scale-[0.99] ${
        compact ? "bottom-4 px-5 py-4 text-xl" : "bottom-5 px-6 py-5 text-2xl"
      }`}
      aria-label="Get a grown-up"
    >
      Get a grown-up
    </button>
  );
}

export default EmergencyButton;
