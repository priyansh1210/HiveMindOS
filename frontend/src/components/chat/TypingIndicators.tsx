import type { Agent, AgentRole, AgentStatus } from "@/lib/types";

export function TypingIndicators({
  agents,
  statuses,
}: {
  agents: Map<string, Agent>;
  statuses: Partial<Record<AgentRole, AgentStatus>>;
}) {
  const busy = Object.entries(statuses).filter(
    ([, status]) => status === "working" || status === "collaborating",
  ) as [AgentRole, AgentStatus][];

  if (busy.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 px-2">
      {busy.map(([role, status]) => {
        const agent = agents.get(role);
        const name = agent?.name ?? role;
        const color = agent?.color ?? "#71717a";
        return (
          <div
            key={role}
            className="flex items-center gap-2 rounded-full border border-zinc-800 bg-zinc-900/60 px-3 py-1 text-xs text-zinc-300"
          >
            <span
              className="inline-block h-2 w-2 rounded-full animate-pulse"
              style={{ backgroundColor: color }}
            />
            <span>{name} is {status === "collaborating" ? "collaborating" : "thinking"}…</span>
          </div>
        );
      })}
    </div>
  );
}
