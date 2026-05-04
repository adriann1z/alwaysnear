"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { AdminShell } from "@/components/admin/AdminShell";
import { Card, TextInput } from "@/components/parent/ui";
import { api } from "@/lib/api";
import { RequireAdmin } from "@/lib/auth";

export default function AdminAuditLogsPage() {
  return (
    <RequireAdmin>
      <AdminShell>
        <AdminAuditLogContent />
      </AdminShell>
    </RequireAdmin>
  );
}

function AdminAuditLogContent() {
  const [action, setAction] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const auditLogs = useQuery({
    queryKey: ["admin-audit-logs", action, startDate, endDate],
    queryFn: () =>
      api.admin.auditLogs({
        action: action || undefined,
        start_date: toDateTime(startDate, "start"),
        end_date: toDateTime(endDate, "end")
      })
  });

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ink/50">
          Admin audit logs
        </p>
        <h1 className="mt-2 text-5xl font-bold">Access and safety events</h1>
      </div>

      <Card>
        <div className="grid gap-4 md:grid-cols-3">
          <label className="space-y-2 text-sm font-semibold">
            Action
            <TextInput
              placeholder="auth.login"
              value={action}
              onChange={(event) => setAction(event.target.value)}
            />
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
        {auditLogs.isLoading && <p className="text-sm text-ink/60">Loading audit logs...</p>}
        {auditLogs.isError && <p className="text-sm text-emergency">Audit logs could not be loaded.</p>}
        {auditLogs.data && auditLogs.data.length > 0 && (
          <div className="max-h-[680px] overflow-auto">
            <table className="w-full min-w-[860px] border-separate border-spacing-y-3 text-left text-sm">
              <thead className="sticky top-0 bg-white text-xs uppercase tracking-[0.14em] text-ink/45">
                <tr>
                  <th className="px-4">Created</th>
                  <th className="px-4">User</th>
                  <th className="px-4">Action</th>
                  <th className="px-4">Metadata summary</th>
                  <th className="px-4">IP address</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.data.map((log) => (
                  <tr key={log.id} className="bg-white">
                    <td className="rounded-l-3xl px-4 py-4 text-ink/70">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-4">{log.actor_email || log.actor_user_id || "System"}</td>
                    <td className="px-4 py-4 font-semibold">{log.action}</td>
                    <td className="px-4 py-4 text-ink/70">{log.metadata_summary || "None"}</td>
                    <td className="rounded-r-3xl px-4 py-4 text-ink/70">{log.ip_address || "Unknown"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {auditLogs.data?.length === 0 && <p className="text-sm text-ink/60">No audit logs match these filters.</p>}
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
