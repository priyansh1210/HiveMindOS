import { api } from "@/lib/api";
import type { Agent, Task } from "@/lib/types";
import { TaskList } from "@/components/tasks/TaskList";

export default async function TasksPage() {
  let tasks: Task[] = [];
  let agents: Agent[] = [];
  let error: string | null = null;

  try {
    const [t, a] = await Promise.all([api.listTasks(), api.listAgents()]);
    tasks = t;
    agents = a;
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to load tasks";
  }

  if (error) {
    return (
      <div className="rounded-xl border border-rose-900/50 bg-rose-950/20 p-6 text-sm text-rose-300">
        <div className="font-semibold mb-1">Couldn&apos;t load tasks</div>
        <div className="text-xs text-rose-400/80 font-mono">{error}</div>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-6xl flex flex-col gap-5">
      <div>
        <h2 className="text-lg font-semibold text-zinc-100">Tasks</h2>
        <p className="text-xs text-zinc-500">
          Every dispatch and its subtask plan. Click a task for the full timeline.
        </p>
      </div>
      <TaskList agents={agents} initialTasks={tasks} />
    </div>
  );
}
