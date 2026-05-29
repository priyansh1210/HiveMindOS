import { api } from "@/lib/api";
import type { Agent, AgentMetric, TaskMetrics } from "@/lib/types";
import { StatTile } from "@/components/analytics/StatTile";
import { TaskStatusChart } from "@/components/analytics/TaskStatusChart";
import { AgentPerformanceChart } from "@/components/analytics/AgentPerformanceChart";
import { LiveActivityFeed } from "@/components/analytics/LiveActivityFeed";

export default async function AnalyticsPage() {
  let metrics: TaskMetrics | null = null;
  let agentMetrics: AgentMetric[] = [];
  let agents: Agent[] = [];
  let error: string | null = null;

  try {
    const [m, am, a] = await Promise.all([
      api.getTaskMetrics(),
      api.getAgentMetrics(),
      api.listAgents(),
    ]);
    metrics = m;
    agentMetrics = am;
    agents = a;
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to load analytics";
  }

  if (error || !metrics) {
    return (
      <div className="rounded-xl border border-rose-900/50 bg-rose-950/20 p-6 text-sm text-rose-300">
        <div className="font-semibold mb-1">Couldn&apos;t load analytics</div>
        <div className="text-xs text-rose-400/80 font-mono">{error}</div>
      </div>
    );
  }

  const totalMessages = agentMetrics.reduce((s, a) => s + a.messages_sent, 0);
  const activeAgents = agentMetrics.filter((a) => a.messages_sent > 0).length;
  const topAgent = agentMetrics[0]; // sorted DESC by messages_sent

  return (
    <div className="mx-auto w-full max-w-6xl flex flex-col gap-5">
      <div>
        <h2 className="text-lg font-semibold text-zinc-100">Analytics</h2>
        <p className="text-xs text-zinc-500">
          Workforce performance and live event stream.
        </p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatTile
          label="Total tasks"
          value={metrics.total_tasks}
          sublabel={`${metrics.completed} completed · ${metrics.failed} failed`}
          accent="#34d399"
        />
        <StatTile
          label="Completion rate"
          value={`${(metrics.completion_rate * 100).toFixed(0)}%`}
          sublabel="of all dispatched tasks"
          accent="#fbbf24"
        />
        <StatTile
          label="Agent messages"
          value={totalMessages}
          sublabel={`${activeAgents}/${agents.length} agents active`}
          accent="#60a5fa"
        />
        <StatTile
          label="Top agent"
          value={topAgent ? topAgent.agent_name.replace(" Agent", "") : "—"}
          sublabel={topAgent ? `${topAgent.messages_sent} messages sent` : ""}
          accent={topAgent?.color ?? "#a78bfa"}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <TaskStatusChart metrics={metrics} />
        <AgentPerformanceChart metrics={agentMetrics} />
      </div>

      <LiveActivityFeed agents={agents} />
    </div>
  );
}
