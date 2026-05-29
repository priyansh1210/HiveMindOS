"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { Agent, Message } from "@/lib/types";
import { useLiveEvents } from "@/hooks/useLiveEvents";
import { MessageBubble } from "./MessageBubble";
import { TypingIndicators } from "./TypingIndicators";

const CONN_STYLE = {
  connecting: { dot: "bg-amber-400 animate-pulse", label: "Connecting…" },
  open: { dot: "bg-emerald-400 animate-pulse", label: "Live" },
  closed: { dot: "bg-rose-500", label: "Disconnected — retrying" },
} as const;

export function ChatFeed({
  agents,
  initialMessages,
}: {
  agents: Agent[];
  initialMessages: Message[];
}) {
  const { connection, messages, agentStatus } = useLiveEvents(initialMessages);

  const agentMap = useMemo(() => {
    const m = new Map<string, Agent>();
    for (const a of agents) m.set(a.role, a);
    return m;
  }, [agents]);

  // Animate only messages that arrive after mount, not the SSR seed.
  const [initialIds] = useState(() => new Set(initialMessages.map((m) => m.id)));

  const scrollerRef = useRef<HTMLDivElement>(null);
  const messageCount = messages.length;

  useEffect(() => {
    const el = scrollerRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messageCount]);

  const conn = CONN_STYLE[connection];

  return (
    <div className="flex flex-col h-[calc(100vh-9rem)] rounded-xl border border-zinc-800 bg-zinc-900/30">
      <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-3">
        <div>
          <div className="text-sm font-semibold text-zinc-100">Live Agent Chat</div>
          <div className="text-xs text-zinc-500">
            {messageCount} message{messageCount === 1 ? "" : "s"} · streaming from /ws
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs text-zinc-400">
          <span className={`inline-block h-2 w-2 rounded-full ${conn.dot}`} />
          {conn.label}
        </div>
      </div>

      <div ref={scrollerRef} className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-4">
        {messageCount === 0 ? (
          <EmptyState />
        ) : (
          messages.map((m) => (
            <div
              key={m.id}
              className={initialIds.has(m.id) ? undefined : "animate-fade-in"}
            >
              <MessageBubble message={m} agents={agentMap} />
            </div>
          ))
        )}
      </div>

      <div className="border-t border-zinc-800 px-4 py-2 min-h-[2.5rem] flex items-center">
        <TypingIndicators agents={agentMap} statuses={agentStatus} />
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="m-auto text-center max-w-md text-sm text-zinc-500">
      <div className="text-base font-semibold text-zinc-300 mb-1">
        No messages yet
      </div>
      Dispatch a task from the dashboard and watch the agents collaborate here in real time.
    </div>
  );
}
