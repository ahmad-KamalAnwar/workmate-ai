import { ErrorNotice, LoadingText } from "@/components/ui";
import type { Task } from "@/lib/api/client";
import type { AsyncState } from "@/lib/use-api";

const statusStyles: Record<Task["status"], string> = {
  pending: "bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-200",
  planning: "bg-sky-100 text-sky-900 dark:bg-sky-950 dark:text-sky-200",
  running: "bg-sky-100 text-sky-900 dark:bg-sky-950 dark:text-sky-200",
  awaiting_approval: "bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-200",
  succeeded: "bg-emerald-100 text-emerald-900 dark:bg-emerald-950 dark:text-emerald-200",
  failed: "bg-red-100 text-red-900 dark:bg-red-950 dark:text-red-200",
  cancelled: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
};

const dateFormat = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" });

export function TaskList({ state, onRetry }: { state: AsyncState<Task[]>; onRetry: () => void }) {
  if (state.status === "loading") return <LoadingText>Loading tasks…</LoadingText>;
  if (state.status === "error") return <ErrorNotice message={state.error.message} onRetry={onRetry} />;
  if (state.data.length === 0) {
    return (
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        No tasks yet. Tasks you give WorkMate will appear here with their status.
      </p>
    );
  }
  return (
    <ul className="divide-y divide-zinc-200 dark:divide-zinc-800">
      {state.data.map((task) => (
        <li key={task.id} className="flex items-center justify-between gap-4 py-3">
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{task.title}</p>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              <time dateTime={task.created_at}>{dateFormat.format(new Date(task.created_at))}</time>
              {" · "}
              {task.source}
            </p>
          </div>
          <span
            className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${statusStyles[task.status]}`}
          >
            {task.status.replace("_", " ")}
          </span>
        </li>
      ))}
    </ul>
  );
}
