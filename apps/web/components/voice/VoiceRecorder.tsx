"use client";

import { useRef, useState } from "react";

import { PrimaryButton, SecondaryButton } from "@/components/parent/ui";

export function VoiceRecorder({
  onRecordingReady
}: {
  onRecordingReady: (file: File) => void;
}) {
  const [recording, setRecording] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  function createPlaceholderRecording() {
    const file = new File([new Blob(["RIFF....WAVEfmt "], { type: "audio/wav" })], "recording.wav", {
      type: "audio/wav"
    });
    onRecordingReady(file);
    setRecording(false);
  }

  return (
    <div className="space-y-4 rounded-[2rem] bg-skysoft p-5">
      <p className="text-sm text-ink/70">
        Record or choose a short audio file. Local placeholder recording is available for setup.
      </p>
      <div className="flex flex-wrap gap-3">
        <PrimaryButton
          onClick={() => {
            setRecording(true);
            window.setTimeout(createPlaceholderRecording, 500);
          }}
        >
          {recording ? "Preparing..." : "Record sample"}
        </PrimaryButton>
        <SecondaryButton onClick={() => inputRef.current?.click()}>Upload audio</SecondaryButton>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="audio/*"
        className="hidden"
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) {
            onRecordingReady(file);
          }
        }}
      />
    </div>
  );
}

export default VoiceRecorder;
