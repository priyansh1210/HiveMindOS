import { api } from "@/lib/api";
import type { Agent, AgentRole } from "@/lib/types";
import { AgentCard } from "./AgentCard";

const ROLE_ORDER: AgentRole[] = ["hr", "sales", "finance", "support", "ops"];

function sortAgents(agents: Agent[]): Agent[] {
  return [...agents].sort(
    (a, b) => ROLE_ORDER.indexOf(a.role) - ROLE_ORDER.indexOf(b.role),
  );
}

export async function AgentGrid() {
  let agents: Agent[] = [];
  let error: string | null = null;

  try {
    agents = sortAgents(await api.listAgents());
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to load agents";
  }

  if (error) {
    return (
      <div className="rounded-xl border border-rose-900/50 bg-rose-950/20 p-6 text-sm text-rose-300">
        <div className="font-semibold mb-1">Couldn&apos;t load agents</div>
        <div className="text-xs text-rose-400/80 font-mono">{error}</div>
        <div className="mt-2 text-xs text-zinc-500">
          Is the backend running on{" "}
          <code className="text-zinc-300">http://localhost:8000</code>?
        </div>
      </div>
    );
  }

  if (agents.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-6 text-sm text-zinc-400">
        No agents found. Seed the database with{" "}
        <code className="text-zinc-200">database/seed.sql</code>.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
      {agents.map((agent) => (
        <AgentCard key={agent.id} agent={agent} />
      ))}
    </div>
  );
}
