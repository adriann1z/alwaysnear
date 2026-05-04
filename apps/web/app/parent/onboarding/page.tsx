"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import { CheckCircle2, HeartHandshake, ShieldCheck, SlidersHorizontal, Trash2, UserCheck } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import {
  Card,
  FieldError,
  PrimaryButton,
  SecondaryButton,
  TextInput
} from "@/components/parent/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const signupSchema = z
  .object({
    email: z.string().email(),
    password: z
      .string()
      .min(12, "Use at least 12 characters")
      .regex(/[A-Z]/, "Add an uppercase letter")
      .regex(/[0-9]/, "Add a number")
      .regex(/[^A-Za-z0-9]/, "Add a special character"),
    confirmPassword: z.string(),
    phone: z.string().optional()
  })
  .refine((values) => values.password === values.confirmPassword, {
    message: "Passwords must match",
    path: ["confirmPassword"]
  });

const profileSchema = z.object({
  firstName: z.string().min(1, "First name is required"),
  parentLabel: z.string().min(1, "Choose what your child calls you"),
  customParentLabel: z.string().optional(),
  relationship: z.string().min(1, "Relationship is required"),
  emergencyPhone: z.string().min(1, "Emergency phone is required")
});

type SignupValues = z.infer<typeof signupSchema>;
type ProfileValues = z.infer<typeof profileSchema>;

const principles = [
  {
    title: "AI comfort helper",
    body: "Always Near offers gentle prompts and familiar reassurance. It never replaces a real grown-up.",
    icon: HeartHandshake
  },
  {
    title: "Honest helper label",
    body: "The helper is described as Mum's Always Near helper, not as the real parent.",
    icon: UserCheck
  },
  {
    title: "Parent control",
    body: "Parents review labels, avatar, voice, comfort scripts, and activation before child use.",
    icon: SlidersHorizontal
  },
  {
    title: "Safety alerts",
    body: "Medium and high-risk signals are surfaced to the parent without exposing full transcripts by default.",
    icon: ShieldCheck
  },
  {
    title: "Deletion rights",
    body: "Voice, avatar, and account data can be removed from the parent privacy area.",
    icon: Trash2
  }
];

const parentLabels = ["Mum", "Mummy", "Dad", "Daddy", "Nana", "Custom"];

export default function ParentOnboardingPage() {
  const [step, setStep] = useState(0);
  const [checks, setChecks] = useState([false, false, false]);
  const router = useRouter();
  const { signup } = useAuth();
  const signupForm = useForm<SignupValues>({ resolver: zodResolver(signupSchema) });
  const profileForm = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: { parentLabel: "Mum", relationship: "Parent/caregiver" }
  });

  const canProceed = checks.every(Boolean);

  async function submitSignup(values: SignupValues) {
    await signup({
      email: values.email,
      password: values.password,
      display_name: "Parent",
      phone: values.phone || null,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC"
    });
    setStep(2);
  }

  async function submitProfile(values: ProfileValues) {
    const label =
      values.parentLabel === "Custom" ? values.customParentLabel?.trim() || "Parent" : values.parentLabel;
    window.localStorage.setItem("always-near-parent-label", label);
    await api.parent.updateProfile({
      display_name: label,
      phone: values.emergencyPhone,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC"
    });
    await api.parent.consent(true);
    router.push("/parent/dashboard");
  }

  return (
    <main className="min-h-screen bg-cream p-5 text-ink md:p-8">
      <div className="mx-auto max-w-5xl">
        <Stepper step={step} />

        {step === 0 && (
          <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}>
            <div className="mb-8">
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ink/50">
                Step 1
              </p>
              <h1 className="mt-2 text-5xl font-bold">Safety First</h1>
            </div>
            <div className="grid gap-4 md:grid-cols-5">
              {principles.map((item) => {
                const Icon = item.icon;
                return (
                  <Card key={item.title} className="md:p-5">
                    <Icon className="mb-4 h-6 w-6" />
                    <h2 className="text-base font-semibold">{item.title}</h2>
                    <p className="mt-2 text-sm leading-6 text-ink/65">{item.body}</p>
                  </Card>
                );
              })}
            </div>
            <Card className="mt-6 space-y-3">
              {[
                "I understand this is an AI comfort helper",
                "I understand it is not a medical, therapy, or emergency service",
                "I am the parent/caregiver or have permission to create this"
              ].map((label, index) => (
                <label key={label} className="flex items-start gap-3 text-sm font-semibold">
                  <input
                    type="checkbox"
                    checked={checks[index]}
                    onChange={(event) => {
                      const next = [...checks];
                      next[index] = event.target.checked;
                      setChecks(next);
                    }}
                    className="mt-1 h-4 w-4"
                  />
                  {label}
                </label>
              ))}
              <PrimaryButton disabled={!canProceed} onClick={() => setStep(1)}>
                Continue
              </PrimaryButton>
            </Card>
          </motion.div>
        )}

        {step === 1 && (
          <Card className="mx-auto max-w-2xl">
            <h1 className="text-4xl font-bold">Create Account</h1>
            <form
              className="mt-6 space-y-4"
              onSubmit={signupForm.handleSubmit(submitSignup)}
            >
              <label className="block text-sm font-semibold">
                Email
                <TextInput className="mt-2" type="email" {...signupForm.register("email")} />
                <FieldError message={signupForm.formState.errors.email?.message} />
              </label>
              <label className="block text-sm font-semibold">
                Password
                <TextInput className="mt-2" type="password" {...signupForm.register("password")} />
                <FieldError message={signupForm.formState.errors.password?.message} />
              </label>
              <label className="block text-sm font-semibold">
                Confirm password
                <TextInput
                  className="mt-2"
                  type="password"
                  {...signupForm.register("confirmPassword")}
                />
                <FieldError message={signupForm.formState.errors.confirmPassword?.message} />
              </label>
              <label className="block text-sm font-semibold">
                Phone
                <TextInput className="mt-2" type="tel" {...signupForm.register("phone")} />
              </label>
              <div className="flex gap-3">
                <SecondaryButton onClick={() => setStep(0)}>Back</SecondaryButton>
                <PrimaryButton type="submit" disabled={signupForm.formState.isSubmitting}>
                  {signupForm.formState.isSubmitting ? "Creating..." : "Create account"}
                </PrimaryButton>
              </div>
            </form>
          </Card>
        )}

        {step === 2 && (
          <Card className="mx-auto max-w-2xl">
            <h1 className="text-4xl font-bold">Parent Profile</h1>
            <form
              className="mt-6 space-y-4"
              onSubmit={profileForm.handleSubmit(submitProfile)}
            >
              <label className="block text-sm font-semibold">
                First name
                <TextInput className="mt-2" {...profileForm.register("firstName")} />
                <FieldError message={profileForm.formState.errors.firstName?.message} />
              </label>
              <label className="block text-sm font-semibold">
                What the child calls the parent
                <select
                  className="mt-2 w-full rounded-3xl border border-ink/10 bg-white px-4 py-3 text-sm"
                  {...profileForm.register("parentLabel")}
                >
                  {parentLabels.map((label) => (
                    <option key={label} value={label}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              {profileForm.watch("parentLabel") === "Custom" && (
                <label className="block text-sm font-semibold">
                  Custom parent label
                  <TextInput className="mt-2" {...profileForm.register("customParentLabel")} />
                </label>
              )}
              <label className="block text-sm font-semibold">
                Relationship to child
                <TextInput className="mt-2" {...profileForm.register("relationship")} />
                <FieldError message={profileForm.formState.errors.relationship?.message} />
              </label>
              <label className="block text-sm font-semibold">
                Emergency phone
                <TextInput className="mt-2" type="tel" {...profileForm.register("emergencyPhone")} />
                <FieldError message={profileForm.formState.errors.emergencyPhone?.message} />
              </label>
              <PrimaryButton type="submit" disabled={profileForm.formState.isSubmitting}>
                {profileForm.formState.isSubmitting ? "Saving..." : "Go to dashboard"}
              </PrimaryButton>
            </form>
          </Card>
        )}
      </div>
    </main>
  );
}

function Stepper({ step }: { step: number }) {
  const labels = ["Safety First", "Create Account", "Parent Profile"];
  return (
    <div className="mb-8 flex gap-3">
      {labels.map((label, index) => (
        <div
          key={label}
          className={`flex flex-1 items-center gap-3 rounded-full px-4 py-3 text-sm font-semibold ${
            index <= step ? "bg-skysoft" : "bg-white/70 text-ink/50"
          }`}
        >
          {index < step ? <CheckCircle2 className="h-4 w-4" /> : <span>{index + 1}</span>}
          <span className="hidden sm:inline">{label}</span>
        </div>
      ))}
    </div>
  );
}
