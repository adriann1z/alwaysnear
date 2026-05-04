import { api } from "@/lib/api";
import type { LiveAvatarSession } from "@/lib/types";

const clientEnabled = process.env.NEXT_PUBLIC_LIVEAVATAR_ENABLED === "true";

export async function startLiveAvatarSession() {
  if (!clientEnabled) {
    return null;
  }
  return api.liveAvatar.startSession();
}

export async function stopLiveAvatarSession(session: LiveAvatarSession | null) {
  if (!session) {
    return;
  }
  await api.liveAvatar.stopSession(session.session_id);
}

export async function playAudioThroughLiveAvatar(
  session: LiveAvatarSession | null,
  audioUrl: string | null
) {
  if (!clientEnabled || !session || !audioUrl || session.mock) {
    return false;
  }
  try {
    const response = await fetch(audioUrl);
    if (!response.ok) {
      return false;
    }
    const audio = await response.blob();
    const result = await api.liveAvatar.speak(session.session_id, audio, audio.type || "audio/wav");
    return result.accepted;
  } catch {
    return false;
  }
}
