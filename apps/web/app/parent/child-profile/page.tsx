"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm, type UseFormRegisterReturn } from "react-hook-form";
import { z } from "zod";

import { ParentShell } from "@/components/parent/ParentShell";
import {
  Card,
  FieldError,
  PrimaryButton,
  TextArea,
  TextInput
} from "@/components/parent/ui";
import { api } from "@/lib/api";
import { RequireAuth } from "@/lib/auth";
import type { ChildProfile } from "@/lib/types";

const schema = z.object({
  name: z.string().min(1, "Child first name is required"),
  ageRange: z.string(),
  communicationStyle: z.string(),
  supportNeeds: z.array(z.string()),
  knownTriggers: z.string().optional(),
  calmingPreferences: z.string().optional(),
  comfortItem: z.string().optional(),
  phrasesLiked: z.string().optional(),
  phrasesToAvoid: z.string().optional()
});

type ChildValues = z.infer<typeof schema>;

const ageRanges = ["Under 3", "3-5", "6-8", "9-12", "13+"];
const communicationStyles = [
  "Speaks clearly",
  "Short phrases",
  "Mostly non-verbal",
  "Picture cards",
  "Mixed"
];
const supportOptions = [
  "Autism",
  "ADHD",
  "Anxiety",
  "Learning disability",
  "Sensory processing difficulty",
  "Speech delay",
  "Physical disability",
  "Other",
  "Prefer not to say"
];

export default function ParentChildProfilePage() {
  return (
    <RequireAuth>
      <ParentShell>
        <ChildProfileContent />
      </ParentShell>
    </RequireAuth>
  );
}

function ChildProfileContent() {
  const [childId, setChildId] = useState<string | null>(null);
  useEffect(() => {
    setChildId(window.localStorage.getItem("always-near-child-id"));
  }, []);

  const child = useQuery({
    queryKey: ["child", childId],
    queryFn: () => api.children.get(childId || ""),
    enabled: Boolean(childId)
  });

  const form = useForm<ChildValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      ageRange: "6-8",
      communicationStyle: "Mixed",
      supportNeeds: []
    }
  });

  useEffect(() => {
    if (child.data) {
      form.reset({
        name: child.data.name,
        ageRange: "6-8",
        communicationStyle: "Mixed",
        supportNeeds: [],
        knownTriggers: child.data.comfort_notes ?? "",
        calmingPreferences: "",
        comfortItem: "",
        phrasesLiked: "",
        phrasesToAvoid: ""
      });
    }
  }, [child.data, form]);

  const save = useMutation({
    mutationFn: async (values: ChildValues) => {
      const comfortNotes = [
        `Age range: ${values.ageRange}`,
        `Communication style: ${values.communicationStyle}`,
        `Support needs: ${values.supportNeeds.join(", ") || "Not specified"}`,
        `Known triggers: ${values.knownTriggers || "Not specified"}`,
        `Calming preferences: ${values.calmingPreferences || "Not specified"}`,
        `Favourite comfort item: ${values.comfortItem || "Not specified"}`,
        `Phrases they like: ${values.phrasesLiked || "Not specified"}`,
        `Phrases to avoid: ${values.phrasesToAvoid || "Not specified"}`
      ].join("\n");
      const payload = { name: values.name, comfort_notes: comfortNotes };
      if (childId) {
        return api.children.update(childId, payload);
      }
      const created = await api.children.create(payload);
      window.localStorage.setItem("always-near-child-id", created.id);
      setChildId(created.id);
      return created;
    },
    onSuccess: () => child.refetch()
  });

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ink/50">
          Child profile
        </p>
        <h1 className="mt-2 text-5xl font-bold">Comfort details</h1>
      </div>
      <Card>
        <form onSubmit={form.handleSubmit((values) => save.mutateAsync(values))} className="space-y-5">
          <label className="block text-sm font-semibold">
            Child first name
            <TextInput className="mt-2" {...form.register("name")} />
            <FieldError message={form.formState.errors.name?.message} />
          </label>

          <div className="grid gap-4 md:grid-cols-2">
            <SelectField label="Age range" values={ageRanges} register={form.register("ageRange")} />
            <SelectField
              label="Communication style"
              values={communicationStyles}
              register={form.register("communicationStyle")}
            />
          </div>

          <fieldset className="rounded-[2rem] bg-skysoft p-5">
            <legend className="mb-3 text-sm font-semibold">Support needs</legend>
            <div className="grid gap-3 md:grid-cols-3">
              {supportOptions.map((option) => (
                <label key={option} className="flex gap-2 text-sm">
                  <input type="checkbox" value={option} {...form.register("supportNeeds")} />
                  {option}
                </label>
              ))}
            </div>
          </fieldset>

          <label className="block text-sm font-semibold">
            Known triggers
            <TextArea className="mt-2" {...form.register("knownTriggers")} />
          </label>
          <label className="block text-sm font-semibold">
            Calming preferences
            <TextArea className="mt-2" {...form.register("calmingPreferences")} />
          </label>
          <label className="block text-sm font-semibold">
            Favourite comfort item
            <TextInput className="mt-2" {...form.register("comfortItem")} />
          </label>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block text-sm font-semibold">
              Phrases they like
              <TextInput className="mt-2" placeholder="Comma-separated tags" {...form.register("phrasesLiked")} />
            </label>
            <label className="block text-sm font-semibold">
              Phrases to avoid
              <TextInput className="mt-2" placeholder="Comma-separated tags" {...form.register("phrasesToAvoid")} />
            </label>
          </div>

          <PrimaryButton type="submit" disabled={save.isPending}>
            {save.isPending ? "Saving..." : "Save child profile"}
          </PrimaryButton>
          {save.isSuccess && <p className="text-sm font-semibold text-emerald-700">Profile saved.</p>}
        </form>
      </Card>
    </div>
  );
}

function SelectField({
  label,
  values,
  register
}: {
  label: string;
  values: string[];
  register: UseFormRegisterReturn;
}) {
  return (
    <label className="block text-sm font-semibold">
      {label}
      <select className="mt-2 w-full rounded-3xl border border-ink/10 bg-white px-4 py-3 text-sm" {...register}>
        {values.map((value) => (
          <option key={value}>{value}</option>
        ))}
      </select>
    </label>
  );
}
