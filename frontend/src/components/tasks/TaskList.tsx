"use client";

import { useMemo, useState } from "react";
import { useLiveEvents } from "@/hooks/useLiveEvents";
import type { Agent, Task, TaskStatus } from "@/lib/types";
import { TaskCard } from "./TaskCard";
import { TaskDetail } from "./TaskDetail";

const FILTERS: { value: TaskStatus | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "in_progress", label: "In progress" },
  { value: "completed", label: "Completed" },
  { value: "pending", label: "Pending" },
  { value: "failed", label: "Failed" },
];

export function TaskList({
  agents,
  initialTasks,
}: {
  agents: Agent[];
  initialTasks: Task[];
}) {
  const [filter, setFilter] = useState<TaskStatus | "all">("all");
  const [selected, setSelected] = useState<string | null>(null);
  const { taskStatus } = useLiveEvents([]);

  // Merge live task_status updates onto the SSR-fetched list.
  const tasks = useMemo(() => {
    return initialTasks
      .map((t) => {
        const update = taskStatus[t.id];
        if (!update) return t;
        return {
          ...t,
          status: update.status,
          completed_at: update.completed_at ?? t.completed_at,
        };
      })
      .sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      );
  }, [initialTasks, taskStatus]);

  const filtered = useMemo(
    () => (filter === "all" ? tasks : tasks.filter((t) => t.status === filter)),
    [tasks, filter],
  );

  const counts = useMemo(() => {
    const c: Record<TaskStatus | "all", number> = {
      all: tasks.length,
      pending: 0,
      in_progress: 0,
      completed: 0,
      failed: 0,
    };
    for (const t of tasks) c[t.status] = (c[t.status] ?? 0) + 1;
    return c;
  }, [tasks]);

  return (
    <>
      <div className="flex items-center gap-2 flex-wrap">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            type="button"
            onClick={() => setFilter(f.value)}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
              filter === f.value
                ? "border-zinc-600 bg-zinc-800 text-zinc-100"
                : "border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:text-zinc-200 hover:border-zinc-700"
            }`}
          >
            {f.label}
            <span className="ml-1.5 text-[10px] text-zinc-500">
              {counts[f.value]}
            </span>
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-8 text-center text-sm text-zinc-500">
          {tasks.length === 0
            ? "No tasks yet. Dispatch one from the dashboard."
            : `No ${filter.replace("_", " ")} tasks.`}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {filtered.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              onClick={() => setSelected(task.id)}
            />
          ))}
        </div>
      )}

      {selected && (
        <TaskDetail
          taskId={selected}
          agents={agents}
          onClose={() => setSelected(null)}
        />
      )}
    </>
  );
}
