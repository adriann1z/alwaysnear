"use client";

import { useEffect, useState } from "react";

import SpeakingAvatar from "@/components/avatar/SpeakingAvatar";
import type { LiveAvatarSession } from "@/lib/types";

export default function LiveAvatarPlayer({
  helperLabel,
  session,
  audioUrl,
  fallbackImageUrl,
  isSpeaking,
  onReady,
  onError,
  onSpeakingStart,
  onSpeakingEnd
}: {
  helperLabel: string;
  session: LiveAvatarSession | null;
  audioUrl?: string | null;
  fallbackImageUrl?: string | null;
  isSpeaking: boolean;
  onReady?: () => void;
  onError?: () => void;
  onSpeakingStart?: () => void;
  onSpeakingEnd?: () => void;
}) {
  const [failed, setFailed] = useState(false);
  const canEmbed = Boolean(session?.embed_url && !session.mock && !failed);

  useEffect(() => {
    if (canEmbed) {
      onReady?.();
    }
  }, [canEmbed, onReady]);

  useEffect(() => {
    if (isSpeaking) {
      onSpeakingStart?.();
      const timeout = window.setTimeout(() => onSpeakingEnd?.(), 2500);
      return () => window.clearTimeout(timeout);
    }
    return undefined;
  }, [isSpeaking, onSpeakingEnd, onSpeakingStart]);

  if (!canEmbed) {
    return (
      <SpeakingAvatar
        helperLabel={helperLabel}
        imageUrl={fallbackImageUrl}
        isSpeaking={isSpeaking}
        audioSrc={audioUrl}
      />
    );
  }

  return (
    <div className="flex flex-col items-center gap-4 rounded-[2rem] bg-skysoft p-6 text-center">
      <iframe
        src={session?.embed_url ?? undefined}
        title="Avatar comfort renderer"
        className="h-64 w-full max-w-sm rounded-[2rem] border-0 bg-white shadow-soft"
        allow="autoplay; encrypted-media"
        onError={() => {
          setFailed(true);
          onError?.();
        }}
      />
      <p className="text-lg font-semibold">{helperLabel}</p>
    </div>
  );
}
