"use client";

import Link from "next/link";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Bell, HeartPulse, MessageSquareHeart, Sparkles, UserRound } from "lucide-react";
import type { ReactNode } from "react";

import { Badge, Card, PrimaryButton, SecondaryButton } from "@/components/parent/ui";
import { ParentShell } from "@/components/parent/ParentShell";
import { RequireAuth, useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import type { AlertItem, ParentProfile } from "@/lib/types";

export default function ParentDashboardPage() {
  return (
    <RequireAuth>
      <ParentShell>
        <DashboardContent />
      </ParentShell>
    </RequireAuth>
  );
}

function DashboardContent() {
  const { user } = useAuth();
  const alerts = useQuery({
    queryKey: ["alerts"],
    queryFn: () => api.alerts.list()
  });
  const profile = useQuery({
    queryKey: ["parent-profile"],
    queryFn: () => api.parent.getProfile()
  });
  const childId = typeof window !== "undefined" ? window.localStorage.getItem("always-near-child-id") : null;
  const helperProfileId =
    typeof window !== "undefined" ? window.localStorage.getItem("always-near-helper-profile-id") : null;
  const conversationId =
    typeof window !== "undefined" ? window.localStorage.getItem("always-near-conversation-id") : null;
  const child = useQuery({
    queryKey: ["child", childId],
    queryFn: () => api.children.get(childId || ""),
    enabled: Boolean(childId)
  });
  const helper = useQuery({
    queryKey: ["helper-profile", helperProfileId],
    queryFn: () => api.helperProfiles.get(helperProfileId || ""),
    enabled: Boolean(helperProfileId)
  });
  const recentConversation = useQuery({
    queryKey: ["conversation-summary", conversationId],
    queryFn: () => api.conversation.summary(conversationId || ""),
    enabled: Boolean(conversationId)
  });
  const pauseHelper = useMutation({
    mutationFn: () => api.helperProfiles.pause(helperProfileId || ""),
    onSuccess: () => helper.refetch()
  });
  const unviewed = alerts.data?.filter((alert) => !alert.parent_viewed) ?? [];
  const latest = alerts.data?.[0];
  const parentLabel =
    profile.data?.display_name ||
    (typeof window !== "undefined" ? window.localStorage.getItem("always-near-parent-label") : null) ||
    "Mum";

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ink/50">
          Dashboard
        </p>
        <h1 className="mt-2 text-5xl font-bold">Hello, {parentLabel}</h1>
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <Card>
          <CardHeader icon={<Sparkles className="h-5 w-5" />} title="Helper Status" />
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <StatusLine label="Helper label" value={helper.data?.label || `${parentLabel}'s Always Near helper`} />
            <StatusLine label="Helper status" value={helper.data?.status || "Pending setup"} />
            <StatusLine label="Script approvals" value="Managed in modes" />
          </div>
          <div className="mt-5 flex items-center justify-between rounded-3xl bg-lavender p-4">
            <span className="text-sm text-ink/70">Script approvals are managed in Comfort Modes.</span>
            <Link href="/parent/helper-setup" className="text-sm font-semibold">
              Continue setup
            </Link>
          </div>
        </Card>

        <Card>
          <CardHeader icon={<UserRound className="h-5 w-5" />} title="Child Profile" />
          <p className="mt-4 text-sm leading-6 text-ink/70">
            {child.isLoading
              ? "Loading child profile..."
              : child.data
                ? `${child.data.name}'s profile is ready. Comfort notes and preferences can be edited any time.`
                : "Add the child's first name, communication style, support needs, calming preferences, and phrases to use or avoid."}
          </p>
          <Link
            href="/parent/child-profile"
            className="mt-5 inline-flex rounded-full bg-ink px-5 py-3 text-sm font-semibold text-white"
          >
            Edit profile
          </Link>
        </Card>

        <Card>
          <CardHeader icon={<Bell className="h-5 w-5" />} title="Safety Alerts" />
          {alerts.isLoading ? (
            <p className="mt-4 text-sm text-ink/60">Loading alerts...</p>
          ) : alerts.isError ? (
            <p className="mt-4 text-sm text-emergency">Could not load alerts yet.</p>
          ) : (
            <div className="mt-5 space-y-4">
              <div className="flex items-center gap-3">
                <span className="text-4xl font-bold">{unviewed.length}</span>
                <span className="text-sm text-ink/65">unchecked alert{unviewed.length === 1 ? "" : "s"}</span>
              </div>
              {latest && (
                <div className="rounded-3xl bg-white p-4">
                  <Badge tone={latest.severity === "HIGH" ? "danger" : "warning"}>
                    {latest.severity}
                  </Badge>
                  <p className="mt-2 text-sm text-ink/75">{latest.trigger_summary}</p>
                </div>
              )}
              <Link href="/parent/alerts" className="text-sm font-semibold">
                Review alerts
              </Link>
            </div>
          )}
        </Card>

        <Card>
          <CardHeader icon={<HeartPulse className="h-5 w-5" />} title="Recent Comfort Sessions" />
          <div className="mt-5 space-y-3">
            {recentConversation.data ? (
              <div className="flex items-center justify-between rounded-3xl bg-white p-4">
                <div>
                  <p className="text-sm font-semibold">Latest comfort session</p>
                  <p className="text-xs text-ink/55">
                    {recentConversation.data.messages.length} messages, no transcript shown here.
                  </p>
                </div>
                <Badge tone="lavender">{recentConversation.data.highest_risk_level || "LOW"}</Badge>
              </div>
            ) : (
              <div className="rounded-3xl bg-white p-4 text-sm text-ink/60">
                Recent comfort sessions will appear after child mode is used.
              </div>
            )}
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader icon={<MessageSquareHeart className="h-5 w-5" />} title="Quick Actions" />
        <div className="mt-5 flex flex-wrap gap-3">
          <Link href="/child" className="rounded-full bg-ink px-5 py-3 text-sm font-semibold text-white">
            Open child mode
          </Link>
          <SecondaryButton
            disabled={!helperProfileId || pauseHelper.isPending}
            onClick={() => pauseHelper.mutate()}
          >
            {pauseHelper.isPending ? "Pausing..." : "Pause helper"}
          </SecondaryButton>
          <PrimaryButton onClick={() => window.alert("Test comfort message will be wired later.")}>
            Test comfort message
          </PrimaryButton>
        </div>
      </Card>
    </div>
  );
}

function CardHeader({ icon, title }: { icon: ReactNode; title: string }) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-11 w-11 items-center justify-center rounded-3xl bg-skysoft">{icon}</div>
      <h2 className="text-xl font-bold">{title}</h2>
    </div>
  );
}

function StatusLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-3xl bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-ink/45">{label}</p>
      <p className="mt-2 text-sm font-semibold">{value}</p>
    </div>
  );
}
