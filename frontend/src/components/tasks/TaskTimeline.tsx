import type { Agent, Subtask } from "@/lib/types";

const STATUS_DOT: Record<Subtask["status"], string> = {
  pending: "bg-zinc-600 border-zinc-700",
  in_progress: "bg-amber-400 border-amber-300 animate-pulse",
  completed: "bg-emerald-400 border-emerald-300",
  failed: "bg-rose-500 border-rose-400",
};

const PRIORITY_STYLE: Record<Subtask["priority"], string> = {
  low: "text-zinc-500",
  medium: "text-zinc-400",
  high: "text-amber-400",
  urgent: "text-rose-400",
};

export function TaskTimeline({
  subtasks,
  agents,
}: {
  subtasks: Subtask[];
  agents: Map<string, Agent>;
}) {
  if (subtasks.length === 0) {
    return (
      <div className="text-sm text-zinc-500 text-center py-8">
        No subtasks yet — orchestrator hasn&apos;t planned this one.
      </div>
    );
  }

  return (
    <ol className="relative flex flex-col gap-4">
      <div className="absolute left-[11px] top-2 bottom-2 w-px bg-zinc-800" aria-hidden />

      {subtasks.map((s, i) => {
        const agent = agents.get(s.assigned_to);
        const agentColor = agent?.color ?? "#71717a";
        const agentLabel = agent?.name ?? s.assigned_to;
        return (
          <li key={s.id} className="relative pl-8">
            <span
              className={`absolute left-0 top-1.5 inline-block h-6 w-6 rounded-full border-2 ${STATUS_DOT[s.status]}`}
              aria-hidden
            />
            <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-3">
              <div className="flex items-center justify-between gap-2 flex-wrap">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-zinc-500">
                    #{i + 1}
                  </span>
                  <span
                    className="inline-flex items-center gap-1.5 text-xs font-medium"
                    style={{ color: agentColor }}
                  >
                    <span
                      className="inline-block h-2 w-2 rounded-full"
                      style={{ backgroundColor: agentColor }}
                    />
                    {agentLabel}
                  </span>
                  {s.depends_on.length > 0 && (
                    <span className="text-[10px] text-zinc-600">
                      depends on #{s.depends_on.join(", #")}
                    </span>
                  )}
                </div>
                <span
                  className={`text-[10px] uppercase tracking-wider ${PRIORITY_STYLE[s.priority]}`}
                >
                  {s.priority}
                </span>
              </div>
              <p className="mt-2 text-sm text-zinc-200">{s.description}</p>
              {s.result && (
                <details className="mt-2 group">
                  <summary className="cursor-pointer text-xs text-zinc-500 hover:text-zinc-300">
                    Result ↓
                  </summary>
                  <pre className="mt-2 text-xs text-zinc-300 whitespace-pre-wrap break-words border-l-2 border-zinc-800 pl-3">
                    {s.result}
                  </pre>
                </details>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
