"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Agent, Task } from "@/lib/types";
import { TaskTimeline } from "./TaskTimeline";

export function TaskDetail({
  taskId,
  agents,
  onClose,
}: {
  taskId: string;
  agents: Agent[];
  onClose: () => void;
}) {
  const [task, setTask] = useState<Task | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const t = await api.getTask(taskId);
        if (!cancelled) setTask(t);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load task");
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [taskId]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const agentMap = new Map<string, Agent>();
  for (const a of agents) agentMap.set(a.role, a);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-3xl max-h-[85vh] overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="absolute top-3 right-3 h-8 w-8 rounded-md text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors flex items-center justify-center text-xl leading-none"
        >
          ×
        </button>

        {error ? (
          <div className="p-6 text-sm text-rose-300">{error}</div>
        ) : !task ? (
          <div className="p-12 text-center text-sm text-zinc-500">Loading task…</div>
        ) : (
          <>
            <div className="px-6 pt-6 pb-4 border-b border-zinc-800">
              <div className="text-xs uppercase tracking-wider text-zinc-500 mb-1">
                Task · {task.status}
              </div>
              <h2 className="text-lg font-semibold text-zinc-100 pr-10">
                {task.title}
              </h2>
              <div className="mt-2 text-[11px] font-mono text-zinc-600">
                id {task.id}
              </div>
            </div>

            <div className="flex-1 overflow-y-auto px-6 py-5 flex flex-col gap-6">
              {task.description && task.description !== task.title && (
                <section>
                  <h3 className="text-xs uppercase tracking-wider text-zinc-500 mb-2">
                    Prompt
                  </h3>
                  <p className="text-sm text-zinc-300 whitespace-pre-wrap">
                    {task.description}
                  </p>
                </section>
              )}

              <section>
                <h3 className="text-xs uppercase tracking-wider text-zinc-500 mb-3">
                  Timeline
                </h3>
                <TaskTimeline
                  subtasks={task.plan?.subtasks ?? []}
                  agents={agentMap}
                />
              </section>

              {task.result?.summary && (
                <section>
                  <h3 className="text-xs uppercase tracking-wider text-zinc-500 mb-2">
                    Summary
                  </h3>
                  <pre className="text-xs text-zinc-300 whitespace-pre-wrap break-words rounded-lg border border-zinc-800 bg-zinc-900/40 p-3">
                    {task.result.summary}
                  </pre>
                </section>
              )}

              {task.result?.error && (
                <section>
                  <h3 className="text-xs uppercase tracking-wider text-rose-400 mb-2">
                    Error
                  </h3>
                  <pre className="text-xs text-rose-300 whitespace-pre-wrap break-words rounded-lg border border-rose-900/50 bg-rose-950/30 p-3">
                    {task.result.error}
                  </pre>
                </section>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
