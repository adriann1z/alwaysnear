"use client";

import { useState } from "react";

import ChildModeShell, { getParentLabel } from "@/components/child/ChildModeShell";

export default function ChildGrownUpPage() {
  const [helpText, setHelpText] = useState("Please find a grown-up near you now.");
  const parentLabel = typeof window !== "undefined" ? getParentLabel() : "Mum";

  return (
    <ChildModeShell compactEmergency>
      <section className="flex min-h-[70vh] flex-col justify-center gap-8 text-center">
        <div className="rounded-[3rem] bg-white p-8 shadow-soft">
          <h1 className="text-5xl font-bold leading-tight text-emergency">
            You need a real grown-up now.
          </h1>
          <p className="mt-6 text-2xl font-semibold">{helpText}</p>
          <button
            type="button"
            onClick={() => setHelpText("Show this screen to a grown-up near you.")}
            className="mt-8 min-h-20 w-full rounded-[2rem] bg-emergency px-6 py-5 text-3xl font-bold text-white"
          >
            Get help
          </button>
        </div>
        <div className="mt-12 rounded-[2rem] bg-skysoft p-6 text-left">
          <p className="text-lg font-semibold">For a grown-up</p>
          <p className="mt-3 text-base leading-7 text-ink/75">
            This child may need your help. Please check on them and contact their parent or
            caregiver. Their parent label in this helper is {parentLabel}.
          </p>
        </div>
      </section>
    </ChildModeShell>
  );
}
