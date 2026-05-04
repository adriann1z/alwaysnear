"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";

import ChildModeShell, { getHelperLabel, getParentLabel } from "@/components/child/ChildModeShell";
import { api } from "@/lib/api";

export default function ChildBedtimePage() {
  const router = useRouter();
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [audioSrc, setAudioSrc] = useState<string | null>(null);
  const parentLabel = typeof window !== "undefined" ? getParentLabel() : "Mum";
  const helperLabel = typeof window !== "undefined" ? getHelperLabel() : "Mum's Always Near helper";
  const text = `It's time to rest. I'm ${helperLabel}. You are safe. ${parentLabel} loves you. Close your eyes and let your body relax.`;

  const bedtimeAudio = useMutation({
    mutationFn: async () => {
      const childId = window.localStorage.getItem("always-near-child-id");
      let conversationId = window.localStorage.getItem("always-near-conversation-id");
      if (!conversationId && childId) {
        const conversation = await api.conversation.start({
          child_id: childId,
          helper_profile_id: window.localStorage.getItem("always-near-helper-profile-id") || null,
          mode: "Bedtime"
        }, false);
        conversationId = conversation.conversation_id;
        window.localStorage.setItem("always-near-conversation-id", conversationId);
      }
      if (!conversationId) {
        return null;
      }
      return api.conversation.message(
        {
          conversation_id: conversationId,
          mode: "Bedtime",
          text: "Bedtime"
        },
        false
      );
    },
    onSuccess: (response) => {
      if (response?.audio_url) {
        setAudioSrc(response.audio_url);
      }
      if (response?.use_emergency_flow) {
        router.push("/child/grown-up");
      }
    }
  });

  useEffect(() => {
    void bedtimeAudio.mutateAsync();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <ChildModeShell dark>
      <section className="flex min-h-[70vh] flex-col items-center justify-center gap-8 text-center">
        <svg viewBox="0 0 320 200" className="h-48 w-full max-w-sm" aria-hidden>
          <rect width="320" height="200" rx="40" fill="#334155" />
          <circle cx="124" cy="86" r="44" fill="#FDE68A" />
          <circle cx="146" cy="72" r="44" fill="#334155" />
          {[48, 220, 252, 282, 78].map((x, index) => (
            <circle key={x} cx={x} cy={40 + index * 24} r="4" fill="#E0F2FE" />
          ))}
        </svg>
        <p className="rounded-[2rem] bg-white/10 p-6 text-3xl font-bold leading-snug">
          {text}
        </p>
        <div className="grid w-full gap-3">
          <button
            type="button"
            onClick={() => void audioRef.current?.play()}
            className="min-h-16 rounded-[2rem] bg-white px-5 py-4 text-2xl font-bold text-ink"
          >
            Hear again
          </button>
          <button
            type="button"
            onClick={() => router.push("/child/grown-up")}
            className="min-h-16 rounded-[2rem] bg-lavender px-5 py-4 text-2xl font-bold text-ink"
          >
            I need help
          </button>
        </div>
        {audioSrc && <audio ref={audioRef} src={audioSrc} className="hidden" />}
      </section>
    </ChildModeShell>
  );
}
