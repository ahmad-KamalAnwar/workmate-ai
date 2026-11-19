"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { LoginForm } from "@/components/login-form";
import { api } from "@/lib/api/client";

export default function LoginPage() {
  const router = useRouter();

  // Already signed in? Go straight to the dashboard.
  useEffect(() => {
    api.me().then(
      () => router.replace("/"),
      () => undefined,
    );
  }, [router]);

  async function signIn(email: string, password: string) {
    await api.login(email, password);
    router.replace("/");
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm rounded-lg border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        <h1 className="text-xl font-semibold">Sign in to WorkMate</h1>
        <p className="mb-6 mt-1 text-sm text-zinc-600 dark:text-zinc-400">Your personal AI work assistant.</p>
        <LoginForm onSubmit={signIn} />
      </div>
    </main>
  );
}
