"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";

import SpeakingAvatar from "@/components/avatar/SpeakingAvatar";
import ChildModeShell, { getHelperLabel } from "@/components/child/ChildModeShell";
import VoiceRecorder from "@/components/voice/VoiceRecorder";
import { api } from "@/lib/api";

type ConversationMessage = {
  response_text: string;
  audio_url?: string | null;
  risk_level: string;
  use_emergency_flow: boolean;
};

export default function ChildTalkPage() {
  const router = useRouter();
  const [mode, setMode] = useState("Talk");
  const [message, setMessage] = useState("Helper is here with you.");
  const [audioSrc, setAudioSrc] = useState<string | null>(null);
  const [status, setStatus] = useState("Getting ready...");
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const initialized = useRef(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const helperLabel = typeof window !== "undefined" ? getHelperLabel() : "Mum's Always Near helper";

  const sendMessage = useMutation({
    mutationFn: async ({ text, audioBase64 }: { text?: string; audioBase64?: string }) => {
      let conversationId = window.localStorage.getItem("always-near-conversation-id");
      const childId = window.localStorage.getItem("always-near-child-id");
      if (!conversationId && childId) {
        const conversation = await api.conversation.start({
          child_id: childId,
          helper_profile_id: window.localStorage.getItem("always-near-helper-profile-id") || null,
          mode
        }, false);
        conversationId = conversation.conversation_id;
        window.localStorage.setItem("always-near-conversation-id", conversationId);
      }
      if (!conversationId) {
        throw new Error("Setup is not finished yet.");
      }
      return api.conversation.message({
        conversation_id: conversationId,
        mode,
        text,
        audio_base64: audioBase64
      }, false);
    },
    onMutate: () => setStatus("Helper is thinking..."),
    onSuccess: (data) => {
      if (data.use_emergency_flow) {
        router.push("/child/grown-up");
        return;
      }
      setMessage(data.response_text);
      setAudioSrc(data.audio_url ?? null);
      if (data.audio_url) {
        setIsSpeaking(true);
        setStatus("Helper is speaking...");
        window.setTimeout(() => setIsSpeaking(false), 2500);
      } else {
        setStatus("Helper is here.");
      }
    },
    onError: () => {
      setStatus("Something went wrong, please try again.");
    }
  });

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const selectedMode = params.get("mode") || "Talk";
    setMode(selectedMode);
    if (!initialized.current) {
      initialized.current = true;
      void sendMessage.mutateAsync({ text: initialTextForMode(selectedMode) });
    }
  }, [sendMessage]);

  function replayAudio() {
    if (audioSrc && audioRef.current) {
      setIsSpeaking(true);
      setStatus("Helper is speaking...");
      void audioRef.current.play();
      window.setTimeout(() => setIsSpeaking(false), 2500);
    }
  }

  async function stopRecordingAndSend() {
    setIsRecording(false);
    setStatus("Helper is thinking...");
    await sendMessage.mutateAsync({ audioBase64: btoa("child voice message") });
  }

  return (
    <ChildModeShell>
      <section className="space-y-6 text-center">
        <SpeakingAvatar helperLabel={helperLabel} isSpeaking={isSpeaking} audioSrc={audioSrc} />
        <div className="rounded-[2rem] bg-white p-6 text-2xl font-bold leading-snug shadow-soft">
          {message}
        </div>
        <p className="min-h-8 text-xl font-semibold text-ink/70">
          {isRecording ? "Recording..." : status}
        </p>
        <div className="grid gap-3">
          <button
            type="button"
            onClick={replayAudio}
            disabled={!audioSrc}
            className="min-h-16 rounded-[2rem] bg-lavender px-5 py-4 text-2xl font-bold disabled:opacity-50"
          >
            Hear it again
          </button>
          <button
            type="button"
            onClick={() => router.push("/child")}
            className="min-h-16 rounded-[2rem] bg-skysoft px-5 py-4 text-2xl font-bold"
          >
            I feel better
          </button>
          <button
            type="button"
            onPointerDown={() => {
              setIsRecording(true);
              setStatus("Recording...");
            }}
            onPointerUp={() => void stopRecordingAndSend()}
            onPointerCancel={() => setIsRecording(false)}
            className="min-h-20 rounded-[2rem] bg-ink px-5 py-4 text-3xl font-bold text-white"
          >
            Talk
          </button>
        </div>
        <VoiceRecorder
          onRecordingReady={async () => {
            await sendMessage.mutateAsync({ audioBase64: btoa("uploaded child voice message") });
          }}
        />
        {audioSrc && <audio ref={audioRef} src={audioSrc} className="hidden" />}
      </section>
    </ChildModeShell>
  );
}

function initialTextForMode(mode: string) {
  if (mode === "Talk") {
    return "I want to talk";
  }
  return mode;
}
