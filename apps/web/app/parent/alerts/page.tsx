"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { ParentShell } from "@/components/parent/ParentShell";
import { Badge, Card, SecondaryButton } from "@/components/parent/ui";
import { api } from "@/lib/api";
import { RequireAuth } from "@/lib/auth";
import type { AlertDetail, AlertItem } from "@/lib/types";

export default function ParentAlertsPage() {
  return (
    <RequireAuth>
      <ParentShell>
        <AlertsContent />
      </ParentShell>
    </RequireAuth>
  );
}

function AlertsContent() {
  const queryClient = useQueryClient();
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const alerts = useQuery({
    queryKey: ["alerts"],
    queryFn: () => api.alerts.list()
  });
  const markViewed = useMutation({
    mutationFn: (id: string) => api.alerts.markViewed(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alerts"] })
  });
  const alertDetail = useQuery({
    queryKey: ["alert-detail", selectedAlertId],
    queryFn: () => api.alerts.get(selectedAlertId || ""),
    enabled: Boolean(selectedAlertId)
  });

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ink/50">
          Safety alerts
        </p>
        <h1 className="mt-2 text-5xl font-bold">Parent checks</h1>
      </div>
      {alerts.isLoading && <Card>Loading alerts...</Card>}
      {alerts.isError && <Card>Alerts could not be loaded yet.</Card>}
      <div className="space-y-4">
        {alerts.data?.map((alert) => (
          <Card key={alert.id}>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="space-y-2">
                <Badge tone={alert.severity === "HIGH" ? "danger" : "warning"}>
                  {alert.severity}
                </Badge>
                <h2 className="text-xl font-bold">{alert.child_name}</h2>
                <p className="text-sm text-ink/70">{alert.trigger_summary}</p>
                <p className="text-xs text-ink/50">
                  {new Date(alert.created_at).toLocaleString()} {alert.mode ? `- ${alert.mode}` : ""}
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <SecondaryButton
                  disabled={alert.parent_viewed || markViewed.isPending}
                  onClick={() => markViewed.mutate(alert.id)}
                >
                  {alert.parent_viewed ? "Checked" : "Mark as checked"}
                </SecondaryButton>
                <button
                  type="button"
                  onClick={() => setSelectedAlertId(alert.id)}
                  className="rounded-full bg-white px-5 py-3 text-sm font-semibold"
                >
                  View full summary
                </button>
              </div>
            </div>
            {selectedAlertId === alert.id && (
              <AlertDetailPanel detail={alertDetail.data} loading={alertDetail.isLoading} />
            )}
          </Card>
        ))}
        {alerts.data?.length === 0 && <Card>No alerts yet.</Card>}
      </div>
    </div>
  );
}

function AlertDetailPanel({
  detail,
  loading
}: {
  detail?: AlertDetail;
  loading: boolean;
}) {
  if (loading) {
    return <p className="mt-4 text-sm text-ink/60">Loading summary...</p>;
  }
  if (!detail) {
    return null;
  }
  return (
    <div className="mt-4 rounded-3xl bg-skysoft p-4 text-sm text-ink/75">
      <p className="font-semibold">Summary</p>
      <p className="mt-2">{detail.trigger_summary || "No summary available."}</p>
      <p className="mt-2 text-xs text-ink/55">Status: {detail.status}</p>
    </div>
  );
}
