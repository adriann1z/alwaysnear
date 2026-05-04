"use client";

import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";

import ChildModeShell, { getParentLabel } from "@/components/child/ChildModeShell";
import { api } from "@/lib/api";

const feelings = [
  { emoji: "😨", label: "Scared", mode: "I feel scared", path: "/child/talk" },
  { emoji: "😢", label: "Sad", mode: "I feel sad", path: "/child/talk" },
  { emoji: "😡", label: "Angry", mode: "I feel angry", path: "/child/talk" },
  { emoji: "😴", label: "Tired", mode: "I feel tired", path: "/child/talk" },
  { emoji: "🔊", label: "Too loud", mode: "It is too loud", path: "/child/breathing" },
  { emoji: "🌙", label: "Bedtime", mode: "Bedtime", path: "/child/bedtime" },
  { emoji: "💬", label: "Talk", mode: "Talk", path: "/child/talk" }
];

export default function ChildPage() {
  const router = useRouter();
  const parentLabel = typeof window !== "undefined" ? getParentLabel() : "Mum";
  const startConversation = useMutation({
    mutationFn: async ({ mode }: { mode: string }) => {
      const childId = window.localStorage.getItem("always-near-child-id");
      if (!childId) {
        throw new Error("Ask a grown-up to finish setup first.");
      }
      return api.conversation.start({
        child_id: childId,
        helper_profile_id: window.localStorage.getItem("always-near-helper-profile-id") || null,
        mode
      }, false);
    }
  });

  async function chooseFeeling(mode: string, path: string) {
    try {
      const conversation = await startConversation.mutateAsync({ mode });
      window.localStorage.setItem("always-near-conversation-id", conversation.conversation_id);
      router.push(`${path}?mode=${encodeURIComponent(mode)}`);
    } catch {
      router.push(`/child/talk?mode=${encodeURIComponent(mode)}&setup=missing`);
    }
  }

  return (
    <ChildModeShell>
      <section className="space-y-6">
        <h1 className="text-center text-5xl font-bold leading-tight">How are you feeling?</h1>
        <div className="grid grid-cols-2 gap-4">
          {feelings.slice(0, 4).map((feeling) => (
            <FeelingButton key={feeling.mode} {...feeling} onChoose={chooseFeeling} />
          ))}
          <FeelingButton
            emoji="💛"
            label={`I miss ${parentLabel}`}
            mode={`I miss ${parentLabel}`}
            path="/child/talk"
            onChoose={chooseFeeling}
          />
          {feelings.slice(4).map((feeling) => (
            <FeelingButton key={feeling.mode} {...feeling} onChoose={chooseFeeling} />
          ))}
        </div>
        {startConversation.isError && (
          <p className="rounded-3xl bg-white p-4 text-center text-lg font-semibold">
            Something went wrong, please try again.
          </p>
        )}
      </section>
    </ChildModeShell>
  );
}

function FeelingButton({
  emoji,
  label,
  mode,
  path,
  onChoose
}: {
  emoji: string;
  label: string;
  mode: string;
  path: string;
  onChoose: (mode: string, path: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onChoose(mode, path)}
      className="min-h-24 rounded-[2rem] bg-white p-4 text-left text-2xl font-bold shadow-soft active:scale-[0.99]"
    >
      <span className="block text-4xl" aria-hidden>
        {emoji}
      </span>
      <span className="mt-2 block">{label}</span>
    </button>
  );
}
