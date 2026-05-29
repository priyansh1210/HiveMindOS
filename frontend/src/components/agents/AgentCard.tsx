import type { Agent, AgentStatus } from "@/lib/types";

const ROLE_BLURB: Record<Agent["role"], string> = {
  hr: "Hiring, onboarding, employee questions, policy",
  sales: "Leads, proposals, competitor analysis, pipeline",
  finance: "Budgets, ROI, invoicing, financial forecasting",
  support: "Customer tickets, escalations, knowledge base",
  ops: "Scheduling, task tracking, workflow, reporting",
};

const STATUS_STYLE: Record<AgentStatus, { dot: string; label: string }> = {
  idle: { dot: "bg-zinc-500", label: "Idle" },
  working: { dot: "bg-amber-400 animate-pulse", label: "Working" },
  collaborating: { dot: "bg-sky-400 animate-pulse", label: "Collaborating" },
  waiting: { dot: "bg-violet-400 animate-pulse", label: "Waiting" },
};

export function AgentCard({ agent }: { agent: Agent }) {
  const status = STATUS_STYLE[agent.status] ?? STATUS_STYLE.idle;
  const initial = agent.name.charAt(0).toUpperCase();

  return (
    <div className="group relative rounded-xl border border-zinc-800 bg-zinc-900/40 p-5 hover:border-zinc-700 transition-colors overflow-hidden">
      <div
        className="absolute inset-x-0 top-0 h-0.5"
        style={{ backgroundColor: agent.color }}
      />
      <div className="flex items-start gap-3">
        <div
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-base font-semibold text-zinc-950"
          style={{ backgroundColor: agent.color }}
        >
          {initial}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-sm font-semibold text-zinc-100 truncate">
              {agent.name}
            </h3>
            <span className="text-[10px] uppercase tracking-wider text-zinc-500">
              {agent.role}
            </span>
          </div>
          <p className="mt-1 text-xs text-zinc-500 leading-relaxed line-clamp-2">
            {ROLE_BLURB[agent.role]}
          </p>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between border-t border-zinc-800 pt-3">
        <div className="flex items-center gap-2 text-xs">
          <span className={`inline-block h-2 w-2 rounded-full ${status.dot}`} />
          <span className="text-zinc-400">{status.label}</span>
        </div>
        <span className="text-[10px] text-zinc-600 font-mono">
          {agent.id.slice(0, 8)}
        </span>
      </div>
    </div>
  );
}
