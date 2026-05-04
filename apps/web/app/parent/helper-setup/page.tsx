"use client";

import { useMemo, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { CheckCircle2 } from "lucide-react";

import SpeakingAvatar from "@/components/avatar/SpeakingAvatar";
import VoicePreview from "@/components/voice/VoicePreview";
import VoiceRecorder from "@/components/voice/VoiceRecorder";
import { ParentShell } from "@/components/parent/ParentShell";
import {
  Card,
  FieldError,
  PrimaryButton,
  SecondaryButton,
  TextInput
} from "@/components/parent/ui";
import { api } from "@/lib/api";
import { RequireAuth } from "@/lib/auth";

const labelOptions = [
  "Mum's Always Near helper",
  "Mummy's Always Near helper",
  "Dad's Always Near helper",
  "Daddy's Always Near helper",
  "Nana's Always Near helper"
];

const forbidden = ["i am", "real", "live", "ai mum", "ai dad"];

export default function ParentHelperSetupPage() {
  return (
    <RequireAuth>
      <ParentShell>
        <HelperSetupContent />
      </ParentShell>
    </RequireAuth>
  );
}

function HelperSetupContent() {
  const [step, setStep] = useState(0);
  const [label, setLabel] = useState(labelOptions[0]);
  const [customLabel, setCustomLabel] = useState("");
  const [avatarChecks, setAvatarChecks] = useState<boolean[]>([false, false, false, false]);
  const [voiceChecks, setVoiceChecks] = useState<boolean[]>([false, false, false, false, false]);
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarId, setAvatarId] = useState<string | null>(null);
  const [voiceId, setVoiceId] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [helperProfileId, setHelperProfileId] = useState<string | null>(null);
  const [liveAvatarId, setLiveAvatarId] = useState("");
  const inputRef = useRef<HTMLInputElement | null>(null);
  const childId = typeof window !== "undefined" ? window.localStorage.getItem("always-near-child-id") : null;
  const selectedLabel = label === "custom" ? customLabel : label;
  const labelError = validateHelperLabel(selectedLabel);

  const createHelper = useMutation({
    mutationFn: async () => {
      if (!childId) {
        return null;
      }
      const response = await api.helperProfiles.create({
        child_id: childId,
        label: selectedLabel,
        description: "Parent-approved Always Near helper"
      });
      window.localStorage.setItem("always-near-helper-profile-id", response.id);
      setHelperProfileId(response.id);
      return response;
    }
  });

  const avatarConsent = useMutation({
    mutationFn: () => api.avatar.consent(true)
  });
  const avatarUpload = useMutation({
    mutationFn: async () => {
      if (!avatarFile) {
        throw new Error("Choose an avatar image first");
      }
      const response = await api.avatar.upload(avatarFile);
      setAvatarId(response.id);
      return response;
    }
  });
  const avatarApprove = useMutation({
    mutationFn: (id: string) => api.avatar.approve(id)
  });

  const voiceConsentUpload = useMutation({
    mutationFn: (file: File) => {
      return api.voice.uploadConsentRecording(file);
    }
  });
  const sampleUpload = useMutation({
    mutationFn: (file: File) => {
      return api.voice.uploadSampleRecording(file);
    }
  });
  const createClone = useMutation({
    mutationFn: async () => {
      const clone = await api.voice.createClone();
      setVoiceId(clone.id);
      return clone;
    }
  });
  const previewVoice = useMutation({
    mutationFn: async () => {
      const id = voiceId || createClone.data?.id;
      if (!id) {
        throw new Error("Create the voice preview first");
      }
      const preview = await api.voice.preview(id, "Mum's Always Near helper is here with a calm reminder.");
      setAudioUrl(preview.signed_url);
      return preview;
    }
  });
  const approveVoice = useMutation({
    mutationFn: () => api.voice.approve(voiceId || createClone.data?.id || "")
  });
  const activateHelper = useMutation({
    mutationFn: () =>
      api.helperProfiles.finalApprove(
        helperProfileId || window.localStorage.getItem("always-near-helper-profile-id") || ""
      )
  });
  const configureLiveAvatar = useMutation({
    mutationFn: () => api.liveAvatar.configure(liveAvatarId)
  });

  const steps = useMemo(
    () => [
      "Helper Label",
      "Avatar Consent",
      "Avatar Capture",
      "Avatar Preview",
      "Voice Consent",
      "Consent Recording",
      "Sample Recording",
      "Voice Preview",
      "Connect LiveAvatar",
      "Final Review"
    ],
    []
  );

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ink/50">Helper setup</p>
        <h1 className="mt-2 text-5xl font-bold">{steps[step]}</h1>
      </div>
      <div className="grid grid-cols-3 gap-2 md:grid-cols-9">
        {steps.map((name, index) => (
          <div
            key={name}
            className={`rounded-full px-3 py-2 text-center text-xs font-semibold ${
              index <= step ? "bg-skysoft" : "bg-white/70 text-ink/45"
            }`}
          >
            {index + 1}
          </div>
        ))}
      </div>

      {step === 0 && (
        <Card>
          <div className="grid gap-3 md:grid-cols-3">
            {labelOptions.map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setLabel(option)}
                className={`rounded-[2rem] border p-5 text-left text-sm font-semibold ${
                  selectedLabel === option ? "border-ink bg-skysoft" : "border-ink/10 bg-white"
                }`}
              >
                {option}
              </button>
            ))}
          </div>
          <label className="mt-5 block text-sm font-semibold">
            Custom helper label
            <TextInput
              className="mt-2"
              value={customLabel}
              onFocus={() => setLabel("custom")}
              onChange={(event) => setCustomLabel(event.target.value)}
              placeholder="Auntie's Always Near helper"
            />
          </label>
          <FieldError message={labelError ?? undefined} />
          <div className="mt-5">
            <PrimaryButton
              disabled={Boolean(labelError) || createHelper.isPending}
              onClick={async () => {
                await createHelper.mutateAsync();
                setStep(1);
              }}
            >
              Save label
            </PrimaryButton>
          </div>
          {!childId && (
            <p className="mt-4 text-sm text-ink/60">
              Add a child profile before final activation. The label can still be prepared here.
            </p>
          )}
        </Card>
      )}

      {step === 1 && (
        <ConsentStep
          checks={avatarChecks}
          setChecks={setAvatarChecks}
          labels={[
            "I have permission to upload this image",
            "The image is appropriate for child comfort",
            "I understand the avatar is reviewed before use",
            "I can delete the avatar later"
          ]}
          onContinue={async () => {
            await avatarConsent.mutateAsync();
            setStep(2);
          }}
        />
      )}

      {step === 2 && (
        <Card>
          <p className="text-sm text-ink/70">Choose a JPEG, PNG, or WEBP image up to 5 MB.</p>
          <div className="mt-5 flex flex-wrap gap-3">
            <SecondaryButton onClick={() => inputRef.current?.click()}>Take selfie</SecondaryButton>
            <PrimaryButton onClick={() => inputRef.current?.click()}>Upload photo</PrimaryButton>
          </div>
          <input
            ref={inputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file && file.size <= 5 * 1024 * 1024) {
                setAvatarFile(file);
              }
            }}
          />
          {avatarFile && <p className="mt-4 text-sm font-semibold">{avatarFile.name}</p>}
          <div className="mt-5">
            <PrimaryButton disabled={!avatarFile} onClick={() => setStep(3)}>
              Preview avatar
            </PrimaryButton>
          </div>
        </Card>
      )}

      {step === 3 && (
        <Card>
          <SpeakingAvatar
            label={selectedLabel}
            imageUrl={avatarFile ? URL.createObjectURL(avatarFile) : null}
          />
          <div className="mt-5 flex flex-wrap gap-3">
            <SecondaryButton onClick={() => setStep(2)}>Retake</SecondaryButton>
            <PrimaryButton
              disabled={avatarUpload.isPending || avatarApprove.isPending}
              onClick={async () => {
                const uploaded = await avatarUpload.mutateAsync();
                await avatarApprove.mutateAsync(uploaded.id);
                setStep(4);
              }}
            >
              Approve avatar
            </PrimaryButton>
          </div>
        </Card>
      )}

      {step === 4 && (
        <ConsentStep
          checks={voiceChecks}
          setChecks={setVoiceChecks}
          labels={[
            "I consent to recording my voice",
            "I understand the voice is used only for the helper",
            "The helper will use honest identity language",
            "I can delete the voice later",
            "I understand this is not for emergency advice"
          ]}
          onContinue={() => setStep(5)}
        />
      )}

      {step === 5 && (
        <Card>
          <p className="mb-4 text-sm font-semibold">
            Consent phrase: I consent to creating a voice for my child&apos;s Always Near helper.
          </p>
          <VoiceRecorder
            onRecordingReady={async (file) => {
              const result = await voiceConsentUpload.mutateAsync(file);
              setVoiceId(result.id);
              setStep(6);
            }}
          />
        </Card>
      )}

      {step === 6 && (
        <Card>
          <p className="mb-4 text-sm font-semibold">
            Sample phrase: You are safe right now. Put your feet on the floor and take one slow breath.
          </p>
          <VoiceRecorder
            onRecordingReady={async (file) => {
              const result = await sampleUpload.mutateAsync(file);
              setVoiceId(result.id);
              setStep(7);
            }}
          />
        </Card>
      )}

      {step === 7 && (
        <Card>
          <VoicePreview audioUrl={audioUrl} />
          <div className="mt-5 flex flex-wrap gap-3">
            <SecondaryButton
              onClick={() => {
                setAudioUrl(null);
                setStep(6);
              }}
            >
              Try again
            </SecondaryButton>
            <PrimaryButton
              onClick={async () => {
                if (!createClone.data) {
                  await createClone.mutateAsync();
                }
                await previewVoice.mutateAsync();
              }}
            >
              Create preview
            </PrimaryButton>
            <PrimaryButton
              disabled={!audioUrl}
              onClick={async () => {
                await approveVoice.mutateAsync();
                setStep(8);
              }}
            >
              Approve voice
            </PrimaryButton>
          </div>
        </Card>
      )}

      {step === 8 && (
        <Card>
          <h2 className="text-2xl font-bold">Connect LiveAvatar</h2>
          <p className="mt-2 text-sm leading-6 text-ink/70">
            Create your LiveAvatar in the LiveAvatar platform, then paste the approved avatar ID
            here. Always Near still handles the child message, safety checks, comfort text, and
            voice audio before avatar rendering.
          </p>
          <label className="mt-5 block text-sm font-semibold">
            LiveAvatar Avatar ID
            <TextInput
              className="mt-2"
              value={liveAvatarId}
              onChange={(event) => setLiveAvatarId(event.target.value)}
              placeholder="Paste approved avatar ID"
            />
          </label>
          <div className="mt-5 flex flex-wrap gap-3">
            <SecondaryButton onClick={() => setStep(9)}>Skip for now</SecondaryButton>
            <PrimaryButton
              disabled={!liveAvatarId.trim() || configureLiveAvatar.isPending}
              onClick={async () => {
                await configureLiveAvatar.mutateAsync();
                setStep(9);
              }}
            >
              Save LiveAvatar ID
            </PrimaryButton>
          </div>
          {configureLiveAvatar.isError && (
            <p className="mt-3 text-sm text-emergency">LiveAvatar ID could not be saved yet.</p>
          )}
        </Card>
      )}

      {step === 9 && (
        <Card>
          <div className="flex items-start gap-4">
            <CheckCircle2 className="h-8 w-8 text-emerald-700" />
            <div>
              <h2 className="text-2xl font-bold">Final Review and Activate</h2>
              <p className="mt-2 text-sm text-ink/70">
                Helper label: {selectedLabel}. Avatar and voice have parent approval. Add a child
                profile if one has not been created yet.
              </p>
            </div>
          </div>
          <div className="mt-5">
            <PrimaryButton
              disabled={!helperProfileId && !window.localStorage.getItem("always-near-helper-profile-id")}
              onClick={async () => {
                await activateHelper.mutateAsync();
                window.location.href = "/parent/dashboard";
              }}
            >
              Activate Always Near helper
            </PrimaryButton>
          </div>
        </Card>
      )}
    </div>
  );
}

function ConsentStep({
  checks,
  setChecks,
  labels,
  onContinue
}: {
  checks: boolean[];
  setChecks: (checks: boolean[]) => void;
  labels: string[];
  onContinue: () => void | Promise<void>;
}) {
  return (
    <Card className="space-y-3">
      {labels.map((label, index) => (
        <label key={label} className="flex gap-3 text-sm font-semibold">
          <input
            type="checkbox"
            checked={checks[index]}
            onChange={(event) => {
              const next = [...checks];
              next[index] = event.target.checked;
              setChecks(next);
            }}
          />
          {label}
        </label>
      ))}
      <PrimaryButton disabled={!checks.every(Boolean)} onClick={() => void onContinue()}>
        Continue
      </PrimaryButton>
    </Card>
  );
}

function validateHelperLabel(label: string) {
  const normalized = label.trim().toLowerCase();
  if (!normalized.endsWith("helper")) {
    return 'Helper label must end with "helper".';
  }
  if (forbidden.some((item) => normalized.includes(item))) {
    return "Helper label uses wording that is not allowed.";
  }
  return null;
}
