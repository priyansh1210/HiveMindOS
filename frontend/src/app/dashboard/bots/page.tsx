import { api } from "@/lib/api";
import type { Agent } from "@/lib/types";
import { BotsPanel } from "@/components/bots/BotsPanel";

export default async function BotsPage() {
  let agents: Agent[] = [];
  let error: string | null = null;

  try {
    agents = await api.listAgents();
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to load agents";
  }

  if (error) {
    return (
      <div className="rounded-xl border border-rose-900/50 bg-rose-950/20 p-6 text-sm text-rose-300">
        <div className="font-semibold mb-1">Couldn&apos;t load agents</div>
        <div className="text-xs text-rose-400/80 font-mono">{error}</div>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-6xl flex flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold text-zinc-100">Bots</h2>
        <p className="text-xs text-zinc-500">
          Chat one-on-one with any specialist. No orchestrator, no other agents
          — just you and the bot.
        </p>
      </div>
      <BotsPanel agents={agents} />
    </div>
  );
}
