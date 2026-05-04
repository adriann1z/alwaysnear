"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { ParentShell } from "@/components/parent/ParentShell";
import { Card, PrimaryButton, SecondaryButton, TextInput } from "@/components/parent/ui";
import { api } from "@/lib/api";
import { RequireAuth } from "@/lib/auth";

export default function ParentPrivacyPage() {
  return (
    <RequireAuth>
      <ParentShell>
        <PrivacyContent />
      </ParentShell>
    </RequireAuth>
  );
}

function PrivacyContent() {
  const [voiceId, setVoiceId] = useState("");
  const [avatarId, setAvatarId] = useState("");
  const [confirmPhrase, setConfirmPhrase] = useState("");
  const confirmation = "DELETE MY ALWAYS NEAR ACCOUNT";
  const exportData = useMutation({
    mutationFn: () => api.data.export(),
    onSuccess: (data) => {
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json"
      });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "always-near-export.json";
      anchor.click();
      URL.revokeObjectURL(url);
    }
  });
  const deleteVoice = useMutation({
    mutationFn: () => api.voice.delete(voiceId)
  });
  const deleteAvatar = useMutation({
    mutationFn: () => api.avatar.delete(avatarId)
  });
  const requestDeletion = useMutation({
    mutationFn: () => api.data.requestDeletion()
  });
  const deleteAccount = useMutation({
    mutationFn: () => api.data.deleteAccount(confirmPhrase)
  });

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ink/50">
          Privacy
        </p>
        <h1 className="mt-2 text-5xl font-bold">Data controls</h1>
      </div>

      <Card>
        <h2 className="text-2xl font-bold">Export data</h2>
        <p className="mt-2 text-sm text-ink/70">
          Request an export of account, child profile, helper setup, comfort mode, and alert data.
        </p>
        <div className="mt-4">
          <PrimaryButton disabled={exportData.isPending} onClick={() => exportData.mutate()}>
            {exportData.isPending ? "Preparing export..." : "Export my data"}
          </PrimaryButton>
        </div>
        {exportData.isError && <p className="mt-3 text-sm text-emergency">Export could not be created.</p>}
        {exportData.isSuccess && <p className="mt-3 text-sm text-ink/60">Your export download has started.</p>}
      </Card>

      <Card>
        <h2 className="text-2xl font-bold">Delete voice</h2>
        <p className="mt-2 text-sm text-ink/70">
          This removes the approved helper voice from future use.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <TextInput value={voiceId} onChange={(event) => setVoiceId(event.target.value)} placeholder="Voice id" />
          <SecondaryButton disabled={!voiceId || deleteVoice.isPending} onClick={() => window.confirm("Delete this voice?") && deleteVoice.mutate()}>
            {deleteVoice.isPending ? "Deleting..." : "Delete voice"}
          </SecondaryButton>
        </div>
        {deleteVoice.isError && <p className="mt-3 text-sm text-emergency">Voice could not be deleted.</p>}
        {deleteVoice.isSuccess && <p className="mt-3 text-sm text-ink/60">Voice deleted.</p>}
      </Card>

      <Card>
        <h2 className="text-2xl font-bold">Delete avatar</h2>
        <p className="mt-2 text-sm text-ink/70">
          This removes the approved helper avatar from future use.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <TextInput value={avatarId} onChange={(event) => setAvatarId(event.target.value)} placeholder="Avatar id" />
          <SecondaryButton disabled={!avatarId || deleteAvatar.isPending} onClick={() => window.confirm("Delete this avatar?") && deleteAvatar.mutate()}>
            {deleteAvatar.isPending ? "Deleting..." : "Delete avatar"}
          </SecondaryButton>
        </div>
        {deleteAvatar.isError && <p className="mt-3 text-sm text-emergency">Avatar could not be deleted.</p>}
        {deleteAvatar.isSuccess && <p className="mt-3 text-sm text-ink/60">Avatar deleted.</p>}
      </Card>

      <Card>
        <h2 className="text-2xl font-bold">Request deletion</h2>
        <p className="mt-2 text-sm text-ink/70">
          This logs a deletion request for your account data. You can continue to full account deletion below.
        </p>
        <div className="mt-4">
          <SecondaryButton disabled={requestDeletion.isPending} onClick={() => requestDeletion.mutate()}>
            {requestDeletion.isPending ? "Sending request..." : "Send deletion request"}
          </SecondaryButton>
        </div>
        {requestDeletion.isError && <p className="mt-3 text-sm text-emergency">Deletion request could not be sent.</p>}
        {requestDeletion.isSuccess && <p className="mt-3 text-sm text-ink/60">Deletion request received.</p>}
      </Card>

      <Card className="border-red-200 bg-red-50">
        <h2 className="text-2xl font-bold text-emergency">Delete account</h2>
        <p className="mt-2 text-sm text-ink/70">
          This is irreversible. Type {confirmation} to confirm account deletion.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <TextInput value={confirmPhrase} onChange={(event) => setConfirmPhrase(event.target.value)} />
          <PrimaryButton
            disabled={confirmPhrase !== confirmation || deleteAccount.isPending}
            onClick={() => window.confirm("Delete this account?") && deleteAccount.mutate()}
          >
            {deleteAccount.isPending ? "Deleting..." : "Delete account"}
          </PrimaryButton>
        </div>
        {deleteAccount.isError && <p className="mt-3 text-sm text-emergency">Account could not be deleted.</p>}
        {deleteAccount.isSuccess && <p className="mt-3 text-sm text-ink/60">Account deleted. Please log in with a different account to continue.</p>}
      </Card>
    </div>
  );
}
