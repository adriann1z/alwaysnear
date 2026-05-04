"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Activity, Bell, Database, Users } from "lucide-react";
import type { ReactNode } from "react";

import { AdminShell } from "@/components/admin/AdminShell";
import { Badge, Card } from "@/components/parent/ui";
import { api } from "@/lib/api";
import { RequireAdmin } from "@/lib/auth";

export default function AdminPage() {
  return (
    <RequireAdmin>
      <AdminShell>
        <AdminDashboard />
      </AdminShell>
    </RequireAdmin>
  );
}

function AdminDashboard() {
  const alerts = useQuery({ queryKey: ["admin-alerts", "dashboard"], queryFn: () => api.admin.alerts() });
  const auditLogs = useQuery({
    queryKey: ["admin-audit-logs", "dashboard"],
    queryFn: () => api.admin.auditLogs({ limit: 8 })
  });
  const users = useQuery({
    queryKey: ["admin-users", "dashboard"],
    queryFn: () => api.admin.users({ limit: 8 })
  });
  const health = useQuery({ queryKey: ["admin-system-health"], queryFn: () => api.admin.systemHealth() });

  const highRisk = alerts.data?.filter((alert) => alert.severity === "HIGH").length ?? 0;
  const mediumRisk = alerts.data?.filter((alert) => alert.severity === "MEDIUM").length ?? 0;

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ink/50">
          Admin dashboard
        </p>
        <h1 className="mt-2 text-5xl font-bold">Safety overview</h1>
      </div>

      <div className="grid gap-5 xl:grid-cols-4">
        <SummaryCard href="/admin/alerts" icon={<Bell className="h-5 w-5" />} label="Total alerts" value={alerts.data?.length ?? 0} loading={alerts.isLoading} />
        <SummaryCard href="/admin/alerts?severity=HIGH" icon={<Bell className="h-5 w-5" />} label="High risk" value={highRisk} tone="danger" loading={alerts.isLoading} />
        <SummaryCard href="/admin/alerts?severity=MEDIUM" icon={<Activity className="h-5 w-5" />} label="Medium risk" value={mediumRisk} tone="warning" loading={alerts.isLoading} />
        <SummaryCard href="/admin/users" icon={<Users className="h-5 w-5" />} label="Users" value={users.data?.length ?? 0} loading={users.isLoading} />
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <Card>
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold">Recent audit activity</h2>
            <Link href="/admin/audit-logs" className="text-sm font-semibold">View logs</Link>
          </div>
          <div className="mt-5 space-y-3">
            {auditLogs.isLoading && <p className="text-sm text-ink/60">Loading audit activity...</p>}
            {auditLogs.isError && <p className="text-sm text-emergency">Audit logs could not be loaded.</p>}
            {auditLogs.data?.map((log) => (
              <div key={log.id} className="rounded-3xl bg-white p-4">
                <p className="text-sm font-semibold">{log.action}</p>
                <p className="text-xs text-ink/55">
                  {new Date(log.created_at).toLocaleString()} {log.actor_email ? `- ${log.actor_email}` : ""}
                </p>
              </div>
            ))}
            {auditLogs.data?.length === 0 && <p className="text-sm text-ink/60">No audit activity yet.</p>}
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-3xl bg-skysoft">
              <Database className="h-5 w-5" />
            </div>
            <h2 className="text-xl font-bold">System health</h2>
          </div>
          <div className="mt-5 space-y-3 rounded-3xl bg-white p-4 text-sm text-ink/70">
            {health.isLoading && <p>Checking API health...</p>}
            {health.isError && <p className="text-emergency">System health could not be loaded.</p>}
            {health.data && (
              <>
                <p>Status: <span className="font-semibold">{health.data.status}</span></p>
                <p>Database: <span className="font-semibold">{health.data.database}</span></p>
                <p>Uptime: <span className="font-semibold">{Math.round(health.data.uptime_seconds)}s</span></p>
              </>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}

function SummaryCard({
  href,
  icon,
  label,
  value,
  loading,
  tone = "lavender"
}: {
  href: string;
  icon: ReactNode;
  label: string;
  value: number;
  loading: boolean;
  tone?: "lavender" | "danger" | "warning";
}) {
  return (
    <Link href={href}>
      <Card className="h-full transition hover:-translate-y-0.5">
        <div className="flex items-center justify-between">
          <div className="flex h-11 w-11 items-center justify-center rounded-3xl bg-skysoft">{icon}</div>
          <Badge tone={tone}>{label}</Badge>
        </div>
        <p className="mt-6 text-4xl font-bold">{loading ? "..." : value}</p>
      </Card>
    </Link>
  );
}
