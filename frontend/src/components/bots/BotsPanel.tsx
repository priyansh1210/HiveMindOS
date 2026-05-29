"use client";

import { useMemo, useState } from "react";
import type { Agent, AgentRole } from "@/lib/types";
import { AgentSelector } from "./AgentSelector";
import { AgentChat } from "./AgentChat";

const ROLE_ORDER: AgentRole[] = ["hr", "sales", "finance", "support", "ops"];

function sortAgents(agents: Agent[]): Agent[] {
  return [...agents].sort(
    (a, b) => ROLE_ORDER.indexOf(a.role) - ROLE_ORDER.indexOf(b.role),
  );
}

export function BotsPanel({ agents }: { agents: Agent[] }) {
  const sorted = useMemo(() => sortAgents(agents), [agents]);
  const [selectedRole, setSelectedRole] = useState<string>(
    sorted[0]?.role ?? "hr",
  );

  const selected = sorted.find((a) => a.role === selectedRole) ?? sorted[0];

  return (
    <div className="flex flex-col lg:flex-row gap-4 h-[calc(100vh-9rem)]">
      <AgentSelector
        agents={sorted}
        selectedRole={selectedRole}
        onSelect={setSelectedRole}
      />
      {selected && <AgentChat key={selected.role} agent={selected} />}
    </div>
  );
}
