import type { Task, TaskStatus } from "@/lib/types";

const STATUS_STYLE: Record<
  TaskStatus,
  { label: string; className: string; dot: string }
> = {
  pending: {
    label: "Pending",
    className: "border-zinc-700 bg-zinc-800/50 text-zinc-300",
    dot: "bg-zinc-500",
  },
  in_progress: {
    label: "In Progress",
    className: "border-amber-700/50 bg-amber-950/30 text-amber-200",
    dot: "bg-amber-400 animate-pulse",
  },
  completed: {
    label: "Completed",
    className: "border-emerald-700/50 bg-emerald-950/30 text-emerald-200",
    dot: "bg-emerald-400",
  },
  failed: {
    label: "Failed",
    className: "border-rose-700/50 bg-rose-950/30 text-rose-200",
    dot: "bg-rose-500",
  },
};

function relativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  const diff = Date.now() - then;
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return `${sec}s ago`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const day = Math.floor(hr / 24);
  return `${day}d ago`;
}

export function TaskCard({
  task,
  onClick,
}: {
  task: Task;
  onClick?: () => void;
}) {
  const style = STATUS_STYLE[task.status] ?? STATUS_STYLE.pending;
  const subtaskCount = task.plan?.subtasks?.length ?? 0;
  const completedSubtasks =
    task.plan?.subtasks?.filter((s) => s.status === "completed").length ?? 0;
  const roles = Array.from(
    new Set(task.plan?.subtasks?.map((s) => s.assigned_to) ?? []),
  );

  return (
    <button
      type="button"
      onClick={onClick}
      className="text-left w-full rounded-xl border border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900/70 hover:border-zinc-700 transition-colors p-4 flex flex-col gap-3"
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-sm font-semibold text-zinc-100 line-clamp-2">
          {task.title}
        </h3>
        <span
          className={`shrink-0 inline-flex items-center gap-1.5 text-[11px] font-medium px-2 py-0.5 rounded-full border ${style.className}`}
        >
          <span className={`inline-block h-1.5 w-1.5 rounded-full ${style.dot}`} />
          {style.label}
        </span>
      </div>

      <div className="flex items-center justify-between text-xs text-zinc-500">
        <div className="flex items-center gap-2 flex-wrap">
          {roles.length > 0 ? (
            roles.map((r) => (
              <span
                key={r}
                className="rounded-md border border-zinc-800 bg-zinc-950 px-1.5 py-0.5 text-[10px] uppercase tracking-wider"
              >
                {r}
              </span>
            ))
          ) : (
            <span className="text-zinc-600">No plan yet</span>
          )}
        </div>
        <div className="flex items-center gap-3 shrink-0">
          {subtaskCount > 0 && (
            <span>
              {completedSubtasks}/{subtaskCount} steps
            </span>
          )}
          <span>{relativeTime(task.created_at)}</span>
        </div>
      </div>
    </button>
  );
}
