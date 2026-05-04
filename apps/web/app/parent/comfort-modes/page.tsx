"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ParentShell } from "@/components/parent/ParentShell";
import { Badge, Card, PrimaryButton, SecondaryButton, TextArea } from "@/components/parent/ui";
import { api } from "@/lib/api";
import { RequireAuth } from "@/lib/auth";
import type { ComfortMode } from "@/lib/types";

export default function ParentComfortModesPage() {
  return (
    <RequireAuth>
      <ParentShell>
        <ComfortModesContent />
      </ParentShell>
    </RequireAuth>
  );
}

function ComfortModesContent() {
  const [childId, setChildId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    setChildId(window.localStorage.getItem("always-near-child-id"));
  }, []);

  const modes = useQuery({
    queryKey: ["comfort-modes", childId],
    queryFn: () => api.comfortModes.list(childId || ""),
    enabled: Boolean(childId)
  });

  const updateMode = useMutation({
    mutationFn: ({ id, script }: { id: string; script: string }) =>
      api.comfortModes.update(id, { script }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["comfort-modes", childId] })
  });
  const safetyCheck = useMutation({
    mutationFn: (id: string) => api.comfortModes.safetyCheck(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["comfort-modes", childId] })
  });
  const approve = useMutation({
    mutationFn: (id: string) => api.comfortModes.approve(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["comfort-modes", childId] })
  });

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ink/50">
          Comfort modes
        </p>
        <h1 className="mt-2 text-5xl font-bold">Scripts and approvals</h1>
      </div>
      {!childId && (
        <Card>
          <p className="text-sm text-ink/70">Create a child profile first to manage comfort modes.</p>
        </Card>
      )}
      {modes.isLoading && <Card>Loading comfort modes...</Card>}
      {modes.isError && <Card>Comfort modes could not be loaded yet.</Card>}
      <div className="space-y-4">
        {modes.data?.map((mode) => (
          <ModeEditor
            key={mode.id}
            mode={mode}
            onSave={(script) => updateMode.mutate({ id: mode.id, script })}
            onSafetyCheck={() => safetyCheck.mutate(mode.id)}
            onApprove={() => approve.mutate(mode.id)}
            busy={updateMode.isPending || safetyCheck.isPending || approve.isPending}
          />
        ))}
      </div>
    </div>
  );
}

function ModeEditor({
  mode,
  onSave,
  onSafetyCheck,
  onApprove,
  busy
}: {
  mode: ComfortMode;
  onSave: (script: string) => void;
  onSafetyCheck: () => void;
  onApprove: () => void;
  busy: boolean;
}) {
  const [script, setScript] = useState(mode.script ?? mode.routine_prompt ?? "");
  useEffect(() => {
    setScript(mode.script ?? mode.routine_prompt ?? "");
  }, [mode.routine_prompt, mode.script]);

  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-bold">{mode.mode_name || mode.name}</h2>
        <div className="flex gap-2">
          <Badge tone={mode.safety_status === "approved" ? "success" : mode.safety_status === "failed" ? "danger" : "warning"}>
            Safety {mode.safety_status}
          </Badge>
          <Badge tone={mode.parent_approval_status === "approved" ? "success" : "warning"}>
            Parent {mode.parent_approval_status}
          </Badge>
        </div>
      </div>
      <TextArea className="mt-4" value={script} onChange={(event) => setScript(event.target.value)} />
      <div className="mt-4 flex flex-wrap gap-3">
        <PrimaryButton disabled={busy} onClick={() => onSave(script)}>
          Save script
        </PrimaryButton>
        <SecondaryButton disabled={busy} onClick={onSafetyCheck}>
          Run safety check
        </SecondaryButton>
        <PrimaryButton
          disabled={busy || mode.safety_status !== "approved"}
          onClick={onApprove}
        >
          Approve
        </PrimaryButton>
      </div>
    </Card>
  );
}
