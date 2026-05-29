import type { Agent, Message } from "@/lib/types";

const TYPE_STYLE: Record<
  string,
  { label: string; className: string }
> = {
  request: { label: "REQUEST", className: "bg-amber-500/10 text-amber-300 border-amber-500/30" },
  response: { label: "RESPONSE", className: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30" },
  info: { label: "INFO", className: "bg-zinc-500/10 text-zinc-300 border-zinc-500/30" },
  escalation: { label: "ESCALATION", className: "bg-rose-500/10 text-rose-300 border-rose-500/30" },
  broadcast: { label: "BROADCAST", className: "bg-sky-500/10 text-sky-300 border-sky-500/30" },
  user: { label: "USER", className: "bg-violet-500/10 text-violet-300 border-violet-500/30" },
};

const DEFAULT_COLOR = "#71717a"; // zinc-500

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return "";
  }
}

function labelFor(roleOrName: string, agents: Map<string, Agent>): string {
  const a = agents.get(roleOrName);
  if (a) return a.name;
  if (roleOrName === "orchestrator") return "Orchestrator";
  if (roleOrName === "user") return "You";
  if (roleOrName === "all") return "All Agents";
  return roleOrName.charAt(0).toUpperCase() + roleOrName.slice(1);
}

function colorFor(role: string, agents: Map<string, Agent>): string {
  if (role === "orchestrator") return "#a3a3a3"; // neutral-400
  if (role === "user") return "#a78bfa"; // violet-400
  return agents.get(role)?.color ?? DEFAULT_COLOR;
}

export function MessageBubble({
  message,
  agents,
}: {
  message: Message;
  agents: Map<string, Agent>;
}) {
  const fromColor = colorFor(message.from_agent, agents);
  const fromLabel = labelFor(message.from_agent, agents);
  const toLabel = labelFor(message.to_agent, agents);
  const initial = fromLabel.charAt(0).toUpperCase();
  const type = TYPE_STYLE[message.message_type] ?? TYPE_STYLE.info;

  return (
    <div className="flex gap-3">
      <div
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-sm font-semibold text-zinc-950"
        style={{ backgroundColor: fromColor }}
        aria-hidden
      >
        {initial}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-semibold text-zinc-100">{fromLabel}</span>
          <span className="text-xs text-zinc-500">→ {toLabel}</span>
          <span
            className={`text-[10px] font-semibold tracking-wider px-1.5 py-0.5 rounded border ${type.className}`}
          >
            {type.label}
          </span>
          <span className="ml-auto text-[11px] text-zinc-600 font-mono">
            {formatTime(message.created_at)}
          </span>
        </div>
        <div className="mt-1 rounded-lg border border-zinc-800 bg-zinc-900/40 px-3 py-2 text-sm text-zinc-200 whitespace-pre-wrap break-words">
          {message.content}
        </div>
      </div>
    </div>
  );
}
