"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Task } from "@/lib/types";
import { useToast } from "@/lib/toast";

const EXAMPLES = [
  "Launch a summer marketing campaign for our new product, budget under $20K",
  "Onboard Priya as a senior frontend engineer starting next Monday",
  "Handle an angry enterprise customer threatening to churn",
];

export function CommandBar() {
  const router = useRouter();
  const { toast } = useToast();
  const [prompt, setPrompt] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recent, setRecent] = useState<Task | null>(null);

  async function submit() {
    const trimmed = prompt.trim();
    if (!trimmed || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const task = await api.createTask(trimmed);
      setRecent(task);
      setPrompt("");
      toast({
        title: "Task dispatched",
        description: task.title,
        variant: "info",
        duration: 3000,
      });
      router.refresh();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to submit task";
      setError(msg);
      toast({
        title: "Dispatch failed",
        description: msg,
        variant: "error",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold text-zinc-100">
            Give your AI workforce a task
          </div>
          <div className="text-xs text-zinc-500">
            Natural language. The orchestrator plans, agents collaborate.
          </div>
        </div>
        {recent && (
          <div className="text-xs text-emerald-400">
            ✓ Task submitted · id {recent.id.slice(0, 8)}
          </div>
        )}
      </div>

      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
            e.preventDefault();
            submit();
          }
        }}
        placeholder="e.g. Launch a summer marketing campaign, budget under $20K"
        rows={3}
        className="w-full resize-none rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-zinc-600"
        disabled={submitting}
      />

      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              type="button"
              onClick={() => setPrompt(ex)}
              className="text-xs px-2.5 py-1 rounded-full border border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-zinc-100 hover:border-zinc-700"
              disabled={submitting}
            >
              {ex.length > 50 ? `${ex.slice(0, 50)}…` : ex}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-zinc-600 hidden sm:inline">
            ⌘/Ctrl + Enter
          </span>
          <button
            onClick={submit}
            disabled={submitting || !prompt.trim()}
            className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-medium text-zinc-950 hover:bg-emerald-400 disabled:bg-zinc-800 disabled:text-zinc-500 disabled:cursor-not-allowed transition-colors"
          >
            {submitting ? "Dispatching…" : "Dispatch task"}
          </button>
        </div>
      </div>

      {error && (
        <div className="text-xs text-rose-400 border border-rose-900/50 bg-rose-950/30 rounded-md px-3 py-2">
          {error}
        </div>
      )}
    </div>
  );
}
