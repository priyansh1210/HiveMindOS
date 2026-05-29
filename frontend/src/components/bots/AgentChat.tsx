"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useToast } from "@/lib/toast";
import type { Agent, AgentToolCall } from "@/lib/types";

interface ChatTurn {
  id: string;
  role: "user" | "agent";
  content: string;
  toolCalls?: AgentToolCall[];
  durationMs?: number;
  error?: string;
}

const SUGGESTIONS: Record<Agent["role"], string[]> = {
  hr: [
    "I'm thinking of hiring a senior backend engineer — what's your process?",
    "What's the standard onboarding checklist for a new designer?",
  ],
  sales: [
    "I have a meeting with Acme Corp tomorrow — give me a quick pitch outline.",
    "How are we doing against our biggest competitor this quarter?",
  ],
  finance: [
    "Estimate a Q3 marketing budget for a $2M ARR startup.",
    "Calculate the ROI on a $40K paid-ads spend that drove $180K in revenue.",
  ],
  support: [
    "A customer is angry their order is 5 days late. Draft a response.",
    "Search the KB for our refund policy.",
  ],
  ops: [
    "Schedule the next sprint kickoff and assign tasks to the team.",
    "Generate a status report for last week's projects.",
  ],
};

export function AgentChat({ agent }: { agent: Agent }) {
  const { toast } = useToast();
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [resetting, setResetting] = useState(false);

  const scrollerRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = scrollerRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [turns.length]);

  async function send(prompt?: string) {
    const text = (prompt ?? draft).trim();
    if (!text || sending) return;

    const userTurn: ChatTurn = {
      id: `u-${Date.now()}`,
      role: "user",
      content: text,
    };
    setTurns((t) => [...t, userTurn]);
    setDraft("");
    setSending(true);

    try {
      const result = await api.invokeAgent(agent.role, text);
      const agentTurn: ChatTurn = {
        id: `a-${Date.now()}`,
        role: "agent",
        content: result.response || "(no response)",
        toolCalls: result.tool_calls,
        durationMs: result.duration_ms,
      };
      setTurns((t) => [...t, agentTurn]);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Request failed";
      setTurns((t) => [
        ...t,
        {
          id: `e-${Date.now()}`,
          role: "agent",
          content: "(failed — see error below)",
          error: msg,
        },
      ]);
      toast({ title: "Agent request failed", description: msg, variant: "error" });
    } finally {
      setSending(false);
    }
  }

  async function reset() {
    setResetting(true);
    try {
      await api.resetAgent(agent.role);
      setTurns([]);
      toast({
        title: `${agent.name} memory cleared`,
        variant: "info",
        duration: 2000,
      });
    } catch (e) {
      toast({
        title: "Reset failed",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    } finally {
      setResetting(false);
    }
  }

  const initial = agent.name.charAt(0);

  return (
    <div className="flex-1 rounded-xl border border-zinc-800 bg-zinc-900/30 flex flex-col min-w-0">
      <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-3">
        <div className="flex items-center gap-3">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-lg text-base font-semibold text-zinc-950"
            style={{ backgroundColor: agent.color }}
          >
            {initial}
          </div>
          <div>
            <div className="text-sm font-semibold text-zinc-100">
              {agent.name}
            </div>
            <div className="text-xs text-zinc-500">
              Direct chat · independent of the orchestrator
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={reset}
          disabled={resetting || (turns.length === 0 && !sending)}
          className="text-xs px-2.5 py-1 rounded border border-zinc-800 text-zinc-400 hover:text-zinc-100 hover:border-zinc-700 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {resetting ? "Resetting…" : "Reset memory"}
        </button>
      </div>

      <div
        ref={scrollerRef}
        className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-4"
      >
        {turns.length === 0 ? (
          <EmptyState agent={agent} onPick={(p) => send(p)} />
        ) : (
          turns.map((t) => (
            <TurnRow key={t.id} turn={t} agentColor={agent.color} />
          ))
        )}
        {sending && (
          <div className="flex gap-3 animate-fade-in">
            <div
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-xs font-semibold text-zinc-950"
              style={{ backgroundColor: agent.color }}
            >
              {initial}
            </div>
            <div className="text-xs text-zinc-500 self-center">
              {agent.name} is thinking…
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-zinc-800 p-3">
        <div className="flex gap-2 items-end">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            placeholder={`Ask ${agent.name} anything…`}
            rows={2}
            disabled={sending}
            className="flex-1 resize-none rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-zinc-600"
          />
          <button
            type="button"
            onClick={() => send()}
            disabled={sending || !draft.trim()}
            className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-medium text-zinc-950 hover:bg-emerald-400 disabled:bg-zinc-800 disabled:text-zinc-500 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>
        <div className="mt-1 text-[10px] text-zinc-600">
          Enter to send · Shift+Enter for newline
        </div>
      </div>
    </div>
  );
}

function EmptyState({
  agent,
  onPick,
}: {
  agent: Agent;
  onPick: (prompt: string) => void;
}) {
  const ideas = SUGGESTIONS[agent.role] ?? [];
  return (
    <div className="m-auto max-w-md text-center">
      <div
        className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl text-xl font-semibold text-zinc-950"
        style={{ backgroundColor: agent.color }}
      >
        {agent.name.charAt(0)}
      </div>
      <h3 className="text-base font-semibold text-zinc-100">
        Talk to {agent.name}
      </h3>
      <p className="mt-1 text-xs text-zinc-500">
        Skip the orchestrator and chat directly with this specialist.
      </p>
      {ideas.length > 0 && (
        <div className="mt-4 flex flex-col gap-2">
          {ideas.map((idea) => (
            <button
              key={idea}
              type="button"
              onClick={() => onPick(idea)}
              className="text-xs text-left rounded-lg border border-zinc-800 bg-zinc-900/60 hover:bg-zinc-800 hover:border-zinc-700 px-3 py-2 text-zinc-300"
            >
              {idea}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function TurnRow({
  turn,
  agentColor,
}: {
  turn: ChatTurn;
  agentColor: string;
}) {
  if (turn.role === "user") {
    return (
      <div className="flex justify-end animate-fade-in">
        <div className="max-w-[80%] rounded-lg bg-zinc-800/80 border border-zinc-700 px-3 py-2 text-sm text-zinc-100 whitespace-pre-wrap break-words">
          {turn.content}
        </div>
      </div>
    );
  }
  return (
    <div className="flex gap-3 animate-fade-in">
      <div
        className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-xs font-semibold text-zinc-950"
        style={{ backgroundColor: agentColor }}
      >
        ●
      </div>
      <div className="min-w-0 flex-1">
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2 text-sm text-zinc-200 whitespace-pre-wrap break-words">
          {turn.content}
        </div>
        {turn.toolCalls && turn.toolCalls.length > 0 && (
          <div className="mt-1.5 flex flex-wrap gap-1">
            {turn.toolCalls.map((tc, i) => (
              <span
                key={i}
                className={`inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded border ${
                  tc.error
                    ? "border-rose-700/50 bg-rose-950/40 text-rose-300"
                    : "border-zinc-700 bg-zinc-900 text-zinc-400"
                }`}
                title={tc.error ?? `${tc.duration_ms}ms`}
              >
                <span>🔧</span>
                <span className="font-mono">{tc.name}</span>
                {!tc.error && (
                  <span className="text-zinc-600">{tc.duration_ms}ms</span>
                )}
              </span>
            ))}
          </div>
        )}
        {typeof turn.durationMs === "number" && (
          <div className="mt-1 text-[10px] text-zinc-600">
            {(turn.durationMs / 1000).toFixed(1)}s
          </div>
        )}
        {turn.error && (
          <pre className="mt-2 text-[11px] text-rose-300 whitespace-pre-wrap break-words border border-rose-900/50 bg-rose-950/30 rounded p-2">
            {turn.error}
          </pre>
        )}
      </div>
    </div>
  );
}
