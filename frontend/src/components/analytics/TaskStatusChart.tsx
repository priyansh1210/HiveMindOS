"use client";

import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { TaskMetrics } from "@/lib/types";

const COLORS = {
  Completed: "#34d399",
  "In progress": "#fbbf24",
  Pending: "#71717a",
  Failed: "#f87171",
};

export function TaskStatusChart({ metrics }: { metrics: TaskMetrics }) {
  const data = [
    { name: "Completed" as const, value: metrics.completed },
    { name: "In progress" as const, value: metrics.in_progress },
    { name: "Pending" as const, value: metrics.pending },
    { name: "Failed" as const, value: metrics.failed },
  ].filter((d) => d.value > 0);

  const pct = (metrics.completion_rate * 100).toFixed(0);

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-zinc-100">Task status</h3>
          <p className="text-xs text-zinc-500">
            {metrics.total_tasks} total · {pct}% completion
          </p>
        </div>
      </div>

      <div className="relative h-56">
        {metrics.total_tasks === 0 ? (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-zinc-500">
            No tasks yet
          </div>
        ) : (
          <>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={2}
                  stroke="#09090b"
                  strokeWidth={2}
                >
                  {data.map((entry) => (
                    <Cell key={entry.name} fill={COLORS[entry.name]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#18181b",
                    border: "1px solid #27272a",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                  itemStyle={{ color: "#e4e4e7" }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <div className="text-2xl font-semibold text-zinc-100">{pct}%</div>
              <div className="text-[10px] uppercase tracking-wider text-zinc-500">
                completed
              </div>
            </div>
          </>
        )}
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
        {(Object.keys(COLORS) as (keyof typeof COLORS)[]).map((name) => {
          const v = data.find((d) => d.name === name)?.value ?? 0;
          return (
            <div key={name} className="flex items-center gap-2">
              <span
                className="inline-block h-2 w-2 rounded-full"
                style={{ backgroundColor: COLORS[name] }}
              />
              <span className="text-zinc-400">{name}</span>
              <span className="ml-auto text-zinc-300 font-mono">{v}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
