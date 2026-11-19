"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { SystemStatus } from "@/components/system-status";
import { TaskList } from "@/components/task-list";
import { Button, Card, ErrorNotice, LoadingText } from "@/components/ui";
import { api } from "@/lib/api/client";
import { useApi } from "@/lib/use-api";

export default function DashboardPage() {
  const router = useRouter();
  const user = useApi(api.me);
  const [signingOut, setSigningOut] = useState(false);
  const [signOutError, setSignOutError] = useState<string | null>(null);

  const unauthenticated = user.status === "error" && user.error.isUnauthenticated;
  useEffect(() => {
    if (unauthenticated) router.replace("/login");
  }, [unauthenticated, router]);

  async function signOut() {
    setSigningOut(true);
    setSignOutError(null);
    try {
      await api.logout();
      router.replace("/login");
    } catch {
      setSignOutError("Sign-out failed. Please try again.");
      setSigningOut(false);
    }
  }

  if (user.status === "loading" || unauthenticated) {
    return (
      <main className="mx-auto max-w-4xl px-4 py-10">
        <LoadingText>Loading…</LoadingText>
      </main>
    );
  }
  if (user.status === "error") {
    return (
      <main className="mx-auto max-w-4xl px-4 py-10">
        <ErrorNotice message={user.error.message} onRetry={user.reload} />
      </main>
    );
  }

  return (
    <>
      <header className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mx-auto flex max-w-4xl items-center justify-between gap-4 px-4 py-3">
          <span className="font-semibold">WorkMate AI</span>
          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-zinc-600 sm:inline dark:text-zinc-400">
              {user.data.display_name ?? user.data.email}
            </span>
            <Button variant="secondary" busy={signingOut} onClick={signOut}>
              {signingOut ? "Signing out…" : "Sign out"}
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-4xl space-y-6 px-4 py-8">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        {signOutError && <ErrorNotice message={signOutError} />}
        <Dashboard />
      </main>
    </>
  );
}

function Dashboard() {
  const readiness = useApi(api.readiness);
  const tasks = useApi(() => api.tasks(10));

  return (
    <>
      <Card
        title="System status"
        labelledBy="status-heading"
        action={
          <Button variant="secondary" onClick={readiness.reload} busy={readiness.status === "loading"}>
            Refresh
          </Button>
        }
      >
        <SystemStatus state={readiness} onRetry={readiness.reload} />
      </Card>
      <Card title="Recent tasks" labelledBy="tasks-heading">
        <TaskList state={tasks} onRetry={tasks.reload} />
      </Card>
    </>
  );
}
