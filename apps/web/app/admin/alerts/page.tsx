"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { AdminShell } from "@/components/admin/AdminShell";
import { Badge, Card, TextInput } from "@/components/parent/ui";
import { api } from "@/lib/api";
import { RequireAdmin } from "@/lib/auth";

export default function AdminAlertsPage() {
  return (
    <RequireAdmin>
      <AdminShell>
        <AdminAlertsContent />
      </AdminShell>
    </RequireAdmin>
  );
}

function AdminAlertsContent() {
  const [severity, setSeverity] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const alerts = useQuery({
    queryKey: ["admin-alerts", severity, startDate, endDate],
    queryFn: () =>
      api.admin.alerts({
        severity: severity || undefined,
        start_date: toDateTime(startDate, "start"),
        end_date: toDateTime(endDate, "end")
      })
  });

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ink/50">
          Admin alerts
        </p>
        <h1 className="mt-2 text-5xl font-bold">Safety alert list</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-ink/65">
          This view shows alert summaries only. Full child transcripts are not displayed here.
        </p>
      </div>

      <Card>
        <div className="grid gap-4 md:grid-cols-3">
          <label className="space-y-2 text-sm font-semibold">
            Severity
            <select
              value={severity}
              onChange={(event) => setSeverity(event.target.value)}
              className="w-full rounded-3xl border border-ink/10 bg-white px-4 py-3 text-sm outline-none"
            >
              <option value="">All</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
            </select>
          </label>
          <label className="space-y-2 text-sm font-semibold">
            Start date
            <TextInput type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
          </label>
          <label className="space-y-2 text-sm font-semibold">
            End date
            <TextInput type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
          </label>
        </div>
      </Card>

      <Card>
        {alerts.isLoading && <p className="text-sm text-ink/60">Loading alerts...</p>}
        {alerts.isError && <p className="text-sm text-emergency">Admin alerts could not be loaded.</p>}
        {alerts.data && alerts.data.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] border-separate border-spacing-y-3 text-left text-sm">
              <thead className="text-xs uppercase tracking-[0.14em] text-ink/45">
                <tr>
                  <th className="px-4">Severity</th>
                  <th className="px-4">Created</th>
                  <th className="px-4">Child label</th>
                  <th className="px-4">Viewed</th>
                  <th className="px-4">Mode</th>
                  <th className="px-4">Trigger summary</th>
                </tr>
              </thead>
              <tbody>
                {alerts.data.map((alert) => (
                  <tr key={alert.id} className="rounded-3xl bg-white">
                    <td className="rounded-l-3xl px-4 py-4">
                      <Badge tone={alert.severity === "HIGH" ? "danger" : "warning"}>
                        {alert.severity}
                      </Badge>
                    </td>
                    <td className="px-4 py-4 text-ink/70">{new Date(alert.created_at).toLocaleString()}</td>
                    <td className="px-4 py-4 font-semibold">{alert.child_label}</td>
                    <td className="px-4 py-4">{alert.parent_viewed ? "Yes" : "No"}</td>
                    <td className="px-4 py-4">{alert.mode || "None"}</td>
                    <td className="rounded-r-3xl px-4 py-4 text-ink/70">{alert.trigger_summary || "No summary"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {alerts.data?.length === 0 && <p className="text-sm text-ink/60">No alerts match these filters.</p>}
      </Card>
    </div>
  );
}

function toDateTime(value: string, boundary: "start" | "end") {
  if (!value) {
    return undefined;
  }
  return `${value}T${boundary === "start" ? "00:00:00" : "23:59:59"}`;
}
