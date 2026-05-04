"use client";

import { motion } from "framer-motion";
import { useEffect, useRef } from "react";

export function SpeakingAvatar({
  imageUrl,
  helperLabel,
  label,
  isSpeaking = false,
  audioSrc
}: {
  imageUrl?: string | null;
  helperLabel?: string;
  label?: string;
  isSpeaking?: boolean;
  audioSrc?: string | null;
}) {
  const displayLabel = helperLabel || label || "Mum's Always Near helper";
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (audioSrc && isSpeaking) {
      void audioRef.current?.play();
    }
  }, [audioSrc, isSpeaking]);

  return (
    <div className="flex flex-col items-center gap-4 rounded-[2rem] bg-skysoft p-6 text-center">
      <motion.div
        animate={isSpeaking ? { scale: [1, 1.04, 1] } : { scale: 1 }}
        transition={{ duration: 1.4, repeat: isSpeaking ? Infinity : 0 }}
        className="rounded-full bg-white/70 p-3"
      >
      <div className="relative flex h-40 w-40 items-center justify-center overflow-hidden rounded-full bg-white shadow-soft">
        {imageUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={imageUrl} alt={`${displayLabel} preview`} className="h-full w-full object-cover" />
        ) : (
          <div className="h-24 w-24 rounded-full bg-lavender" />
        )}
        <motion.div
          animate={isSpeaking ? { scaleX: [1, 1.4, 1], opacity: [0.55, 1, 0.55] } : {}}
          transition={{ duration: 0.45, repeat: isSpeaking ? Infinity : 0 }}
          className="absolute bottom-10 h-3 w-12 rounded-full bg-ink/70"
        />
      </div>
      </motion.div>
      <div>
        <p className="text-lg font-semibold">{displayLabel}</p>
        <p className="text-sm text-ink/70">A gentle comfort helper.</p>
      </div>
      {audioSrc && <audio ref={audioRef} src={audioSrc} className="hidden" />}
    </div>
  );
}

export default SpeakingAvatar;
