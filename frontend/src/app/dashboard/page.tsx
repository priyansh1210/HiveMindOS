import { Suspense } from "react";
import { AgentGrid } from "@/components/agents/AgentGrid";
import { CommandBar } from "@/components/layout/CommandBar";

export default function DashboardPage() {
  return (
    <div className="mx-auto w-full max-w-7xl flex flex-col gap-6">
      <CommandBar />

      <section>
        <div className="mb-4 flex items-end justify-between">
          <div>
            <h2 className="text-lg font-semibold text-zinc-100">Agents</h2>
            <p className="text-xs text-zinc-500">
              Five specialists ready to collaborate.
            </p>
          </div>
        </div>
        <Suspense fallback={<AgentGridSkeleton />}>
          <AgentGrid />
        </Suspense>
      </section>
    </div>
  );
}

function AgentGridSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className="h-32 rounded-xl border border-zinc-800 bg-zinc-900/30 animate-pulse"
        />
      ))}
    </div>
  );
}
