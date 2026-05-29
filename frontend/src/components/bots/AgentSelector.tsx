"use client";

import type { Agent } from "@/lib/types";

const ROLE_BLURB: Record<Agent["role"], string> = {
  hr: "Hiring, onboarding, policy",
  sales: "Leads, proposals, outreach",
  finance: "Budgets, ROI, forecasting",
  support: "Tickets, escalations, KB",
  ops: "Scheduling, workflow, reports",
};

export function AgentSelector({
  agents,
  selectedRole,
  onSelect,
}: {
  agents: Agent[];
  selectedRole: string;
  onSelect: (role: string) => void;
}) {
  return (
    <div className="lg:w-64 shrink-0 rounded-xl border border-zinc-800 bg-zinc-900/30 p-2 flex lg:flex-col gap-1 overflow-x-auto lg:overflow-y-auto">
      {agents.map((a) => {
        const active = a.role === selectedRole;
        return (
          <button
            key={a.role}
            type="button"
            onClick={() => onSelect(a.role)}
            className={`shrink-0 lg:w-full text-left rounded-lg px-3 py-2.5 flex items-center gap-3 transition-colors ${
              active
                ? "bg-zinc-800 border border-zinc-700"
                : "hover:bg-zinc-800/50 border border-transparent"
            }`}
          >
            <div
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-sm font-semibold text-zinc-950"
              style={{ backgroundColor: a.color }}
            >
              {a.name.charAt(0)}
            </div>
            <div className="min-w-0 flex-1 hidden lg:block">
              <div className="text-sm font-semibold text-zinc-100 truncate">
                {a.name}
              </div>
              <div className="text-[11px] text-zinc-500 truncate">
                {ROLE_BLURB[a.role]}
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
