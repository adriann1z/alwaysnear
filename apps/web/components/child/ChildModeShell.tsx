"use client";

import type { ReactNode } from "react";

import EmergencyButton from "@/components/safety/EmergencyButton";

export function getParentLabel() {
  if (typeof window === "undefined") {
    return "Mum";
  }
  return window.localStorage.getItem("always-near-parent-label") || "Mum";
}

export function getHelperLabel() {
  const parentLabel = getParentLabel();
  if (parentLabel.toLowerCase().endsWith("always near helper")) {
    return parentLabel;
  }
  return `${parentLabel}'s Always Near helper`;
}

export function ChildModeShell({
  children,
  dark = false,
  compactEmergency = false
}: {
  children: ReactNode;
  dark?: boolean;
  compactEmergency?: boolean;
}) {
  const helperLabel = getHelperLabel();

  return (
    <main
      className={`min-h-screen pb-32 ${
        dark ? "bg-[#1E293B] text-white" : "bg-cream text-ink"
      }`}
    >
      <header className="sticky top-0 z-30 px-4 py-4">
        <div
          className={`mx-auto max-w-3xl rounded-[2rem] px-5 py-4 text-center text-lg font-bold shadow-soft ${
            dark ? "bg-white/10 text-white" : "bg-white/80 text-ink"
          }`}
        >
          {helperLabel}
        </div>
      </header>
      <div className="mx-auto max-w-3xl px-4 py-4">{children}</div>
      <EmergencyButton compact={compactEmergency} />
    </main>
  );
}

export default ChildModeShell;
