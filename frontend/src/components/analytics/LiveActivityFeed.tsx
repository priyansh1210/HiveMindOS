"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useLiveEvents } from "@/hooks/useLiveEvents";
import type { Agent, Message } from "@/lib/types";

type Activity =
  | { kind: "message"; id: string; ts: string; from: string; to: string; type: string; preview: string }
  | { kind: "agent_status"; id: string; ts: string; role: string; status: string }
  | { kind: "task_status"; id: string; ts: string; taskId: string; status: string };

function nameOf(role: string, agents: Map<string, Agent>): string {
  if (role === "orchestrator") return "Orchestrator";
  if (role === "user") return "You";
  if (role === "all") return "All Agents";
  return agents.get(role)?.name ?? role;
}

function colorOf(role: string, agents: Map<string, Agent>): string {
  if (role === "orchestrator") return "#a3a3a3";
  if (role === "user") return "#a78bfa";
  return agents.get(role)?.color ?? "#71717a";
}

function fmtTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return "";
  }
}

const MAX_ITEMS = 80;

export function LiveActivityFeed({ agents }: { agents: Agent[] }) {
  const { connection, messages, agentStatus, taskStatus } = useLiveEvents([]);
  const [extras, setExtras] = useState<Activity[]>([]);
  const seenAgentStatus = useRef<Set<string>>(new Set());
  const seenTaskStatus = useRef<Set<string>>(new Set());

  const agentMap = useMemo(() => {
    const m = new Map<string, Agent>();
    for (const a of agents) m.set(a.role, a);
    return m;
  }, [agents]);

  // Capture agent_status transitions as their own activity entries.
  useEffect(() => {
    const additions: Activity[] = [];
    for (const [role, status] of Object.entries(agentStatus)) {
      if (!status) continue;
      const key = `${role}:${status}`;
      if (seenAgentStatus.current.has(key)) continue;
      seenAgentStatus.current.add(key);
      additions.push({
        kind: "agent_status",
        id: `agent-${key}-${Date.now()}`,
        ts: new Date().toISOString(),
        role,
        status,
      });
    }
    if (additions.length) {
      setExtras((prev) => [...prev, ...additions].slice(-MAX_ITEMS));
    }
  }, [agentStatus]);

  // Capture task_status transitions.
  useEffect(() => {
    const additions: Activity[] = [];
    for (const [taskId, ev] of Object.entries(taskStatus)) {
      const key = `${taskId}:${ev.status}`;
      if (seenTaskStatus.current.has(key)) continue;
      seenTaskStatus.current.add(key);
      additions.push({
        kind: "task_status",
        id: `task-${key}`,
        ts: ev.completed_at ?? new Date().toISOString(),
        taskId,
        status: ev.status,
      });
    }
    if (additions.length) {
      setExtras((prev) => [...prev, ...additions].slice(-MAX_ITEMS));
    }
  }, [taskStatus]);

  // Merge live messages + extras, sorted by ts.
  const activities = useMemo(() => {
    const msgItems: Activity[] = messages.map((m: Message) => ({
      kind: "message",
      id: m.id,
      ts: m.created_at,
      from: m.from_agent,
      to: m.to_agent,
      type: m.message_type,
      preview: m.content.slice(0, 90),
    }));
    return [...msgItems, ...extras]
      .sort((a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime())
      .slice(-MAX_ITEMS);
  }, [messages, extras]);

  const scrollerRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = scrollerRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [activities.length]);

  const connDot = {
    connecting: "bg-amber-400 animate-pulse",
    open: "bg-emerald-400 animate-pulse",
    closed: "bg-rose-500",
  }[connection];

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 flex flex-col h-[28rem]">
      <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-3">
        <div>
          <h3 className="text-sm font-semibold text-zinc-100">Live activity</h3>
          <p className="text-xs text-zinc-500">
            {activities.length} event{activities.length === 1 ? "" : "s"} this session
          </p>
        </div>
        <span className={`inline-block h-2 w-2 rounded-full ${connDot}`} />
      </div>

      <div
        ref={scrollerRef}
        className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-1.5 font-mono text-[11px]"
      >
        {activities.length === 0 ? (
          <div className="m-auto text-center text-zinc-500 text-xs font-sans">
            Waiting for events… dispatch a task to see live activity.
          </div>
        ) : (
          activities.map((a) => (
            <div key={a.id} className="animate-slide-in">
              <ActivityRow item={a} agents={agentMap} />
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function ActivityRow({
  item,
  agents,
}: {
  item: Activity;
  agents: Map<string, Agent>;
}) {
  const ts = fmtTime(item.ts);
  if (item.kind === "message") {
    const color = colorOf(item.from, agents);
    return (
      <div className="flex gap-2">
        <span className="text-zinc-600 shrink-0">{ts}</span>
        <span className="shrink-0" style={{ color }}>
          {nameOf(item.from, agents)}
        </span>
        <span className="text-zinc-600 shrink-0">→</span>
        <span className="text-zinc-400 shrink-0">{nameOf(item.to, agents)}</span>
        <span className="text-zinc-500 truncate">: {item.preview}</span>
      </div>
    );
  }
  if (item.kind === "agent_status") {
    const color = colorOf(item.role, agents);
    return (
      <div className="flex gap-2">
        <span className="text-zinc-600 shrink-0">{ts}</span>
        <span className="text-zinc-600 shrink-0">●</span>
        <span style={{ color }}>{nameOf(item.role, agents)}</span>
        <span className="text-zinc-500">→ {item.status}</span>
      </div>
    );
  }
  return (
    <div className="flex gap-2">
      <span className="text-zinc-600 shrink-0">{ts}</span>
      <span className="text-zinc-600 shrink-0">▤</span>
      <span className="text-zinc-300">
        task {item.taskId.slice(0, 8)}
      </span>
      <span className="text-zinc-500">→ {item.status}</span>
    </div>
  );
}
