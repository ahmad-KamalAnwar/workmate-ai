import { ErrorNotice, LoadingText } from "@/components/ui";
import type { Readiness } from "@/lib/api/client";
import type { AsyncState } from "@/lib/use-api";

const labels: Record<string, string> = { database: "Database", redis: "Redis (job queue)" };

export function SystemStatus({ state, onRetry }: { state: AsyncState<Readiness>; onRetry: () => void }) {
  if (state.status === "loading") return <LoadingText>Checking services…</LoadingText>;
  if (state.status === "error") return <ErrorNotice message={state.error.message} onRetry={onRetry} />;

  const { checks, status } = state.data;
  return (
    <div className="space-y-3">
      <p className="text-sm">
        Overall:{" "}
        <strong className={status === "ok" ? "text-emerald-700 dark:text-emerald-400" : "text-red-700 dark:text-red-400"}>
          {status === "ok" ? "All services operational" : "Degraded"}
        </strong>
      </p>
      <dl className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {Object.entries(checks).map(([name, result]) => (
          <div
            key={name}
            className="flex items-center justify-between rounded-md border border-zinc-200 px-3 py-2 text-sm dark:border-zinc-800"
          >
            <dt>{labels[name] ?? name}</dt>
            <dd className="flex items-center gap-2">
              <span
                aria-hidden="true"
                className={`h-2 w-2 rounded-full ${result === "ok" ? "bg-emerald-500" : "bg-red-500"}`}
              />
              {result === "ok" ? "Connected" : "Unavailable"}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
