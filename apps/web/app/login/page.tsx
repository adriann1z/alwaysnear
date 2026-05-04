"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Card, FieldError, PrimaryButton, TextInput } from "@/components/parent/ui";
import { useAuth } from "@/lib/auth";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(1, "Password is required")
});

type LoginValues = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const { login, error } = useAuth();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting }
  } = useForm<LoginValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: LoginValues) {
    try {
      await login(values);
      router.push("/parent/dashboard");
    } catch (error) {
      setError("root", {
        message: error instanceof Error ? error.message : "Could not log in"
      });
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-cream p-6 text-ink">
      <Card className="w-full max-w-md">
        <div className="mb-8">
          <p className="text-sm font-semibold text-ink/60">Welcome back</p>
          <h1 className="mt-2 text-4xl font-bold">Log in</h1>
        </div>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <label className="block text-sm font-semibold">
            Email
            <TextInput className="mt-2" type="email" {...register("email")} />
            <FieldError message={errors.email?.message} />
          </label>
          <label className="block text-sm font-semibold">
            Password
            <TextInput className="mt-2" type="password" {...register("password")} />
            <FieldError message={errors.password?.message} />
          </label>
          <FieldError message={errors.root?.message || error || undefined} />
          <PrimaryButton type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Checking..." : "Log in"}
          </PrimaryButton>
        </form>
        <p className="mt-6 text-sm text-ink/65">
          New here?{" "}
          <Link href="/parent/onboarding" className="font-semibold text-ink">
            Create an account
          </Link>
        </p>
      </Card>
    </main>
  );
}
