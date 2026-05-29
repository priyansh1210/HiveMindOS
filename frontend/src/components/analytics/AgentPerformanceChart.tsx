"use client";

import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { AgentMetric } from "@/lib/types";

export function AgentPerformanceChart({ metrics }: { metrics: AgentMetric[] }) {
  const data = metrics.map((m) => ({
    name: m.agent_name.replace(" Agent", ""),
    messages: m.messages_sent,
    tasks: m.tasks_touched,
    color: m.color ?? "#71717a",
  }));

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-zinc-100">
          Agent activity
        </h3>
        <p className="text-xs text-zinc-500">
          Messages sent per agent (all-time)
        </p>
      </div>

      <div className="h-64">
        {data.length === 0 ? (
          <div className="h-full flex items-center justify-center text-sm text-zinc-500">
            No agent activity yet
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              layout="vertical"
              margin={{ top: 4, right: 16, bottom: 4, left: 16 }}
            >
              <XAxis
                type="number"
                stroke="#52525b"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                type="category"
                dataKey="name"
                stroke="#a1a1aa"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                width={70}
              />
              <Tooltip
                cursor={{ fill: "#27272a", opacity: 0.4 }}
                contentStyle={{
                  backgroundColor: "#18181b",
                  border: "1px solid #27272a",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
                itemStyle={{ color: "#e4e4e7" }}
                formatter={(value, name) => [
                  value as number,
                  name === "messages" ? "Messages" : String(name),
                ]}
              />
              <Bar dataKey="messages" radius={[0, 6, 6, 0]}>
                {data.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="mt-4 border-t border-zinc-800 pt-3 grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
        {metrics.map((m) => (
          <div key={m.role}>
            <div
              className="text-[10px] uppercase tracking-wider"
              style={{ color: m.color ?? "#a1a1aa" }}
            >
              {m.role}
            </div>
            <div className="text-zinc-300 mt-0.5">
              {m.tasks_touched} task{m.tasks_touched === 1 ? "" : "s"}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
