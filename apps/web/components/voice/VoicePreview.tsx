"use client";

export function VoicePreview({ audioUrl }: { audioUrl?: string | null }) {
  return (
    <div className="rounded-[2rem] bg-lavender p-5">
      <p className="mb-3 text-sm font-semibold">Voice preview</p>
      {audioUrl ? (
        <audio controls src={audioUrl} className="w-full" />
      ) : (
        <p className="text-sm text-ink/65">A preview will appear here after the voice sample is ready.</p>
      )}
    </div>
  );
}

export default VoicePreview;
