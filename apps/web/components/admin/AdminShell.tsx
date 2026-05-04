"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, Bell, HeartHandshake, Shield, UserRoundCog } from "lucide-react";
import type { ReactNode } from "react";

import { useAuth } from "@/lib/auth";

const navItems = [
  { href: "/admin", label: "Dashboard", icon: Shield },
  { href: "/admin/alerts", label: "Alerts", icon: Bell },
  { href: "/admin/audit-logs", label: "Audit Logs", icon: Activity },
  { href: "/admin/users", label: "Users", icon: UserRoundCog }
];

export function AdminShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-cream text-ink">
      <div className="flex min-h-screen">
        <aside className="hidden w-72 shrink-0 border-r border-white/70 bg-white/65 p-5 backdrop-blur lg:block">
          <Link href="/admin" className="flex items-center gap-3 rounded-[2rem] px-2 py-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-3xl bg-skysoft">
              <HeartHandshake className="h-5 w-5" />
            </div>
            <div>
              <p className="text-lg font-semibold">Always Near</p>
              <p className="text-xs text-ink/60">Admin portal</p>
            </div>
          </Link>
          <nav className="mt-8 space-y-2">
            {navItems.map((item) => {
              const active = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 rounded-3xl px-4 py-3 text-sm font-medium transition ${
                    active ? "bg-lavender text-ink shadow-soft" : "text-ink/70 hover:bg-white"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>
        <main className="min-w-0 flex-1">
          <header className="sticky top-0 z-10 flex items-center justify-between border-b border-white/70 bg-cream/85 px-5 py-4 backdrop-blur md:px-8">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ink/50">
                Admin area
              </p>
              <p className="text-sm text-ink/70">{user?.email ?? "Signed in"}</p>
            </div>
            <span className="rounded-full bg-ink px-4 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-white">
              {user?.role ?? "admin"}
            </span>
          </header>
          <div className="p-5 md:p-8">{children}</div>
        </main>
      </div>
    </div>
  );
}
