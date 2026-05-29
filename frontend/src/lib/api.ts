import type {
  Agent,
  AgentMetric,
  Message,
  Task,
  TaskMetrics,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

async function jsonFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => jsonFetch<{ status: string; environment: string }>("/health"),

  listAgents: () => jsonFetch<Agent[]>("/api/agents"),

  listTasks: () => jsonFetch<Task[]>("/api/tasks"),

  getTask: (id: string) => jsonFetch<Task>(`/api/tasks/${id}`),

  createTask: (prompt: string) =>
    jsonFetch<Task>("/api/tasks", {
      method: "POST",
      body: JSON.stringify({ prompt }),
    }),

  listMessages: (taskId?: string) =>
    jsonFetch<Message[]>(
      taskId ? `/api/messages?task_id=${encodeURIComponent(taskId)}` : "/api/messages",
    ),

  getTaskMetrics: () => jsonFetch<TaskMetrics>("/api/analytics/tasks"),

  getAgentMetrics: () => jsonFetch<AgentMetric[]>("/api/analytics/agents"),
};

export function wsUrl(): string {
  const base = API_BASE.replace(/^http/, "ws");
  return `${base}/ws`;
}
