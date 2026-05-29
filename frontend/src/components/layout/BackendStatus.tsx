"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type State = "checking" | "online" | "offline";

export function BackendStatus() {
  const [state, setState] = useState<State>("checking");

  useEffect(() => {
    let cancelled = false;
    const ping = async () => {
      try {
        await api.health();
        if (!cancelled) setState("online");
      } catch {
        if (!cancelled) setState("offline");
      }
    };
    ping();
    const interval = setInterval(ping, 10_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const config = {
    checking: { dot: "bg-zinc-500", label: "Connecting…" },
    online: { dot: "bg-emerald-400", label: "Backend online" },
    offline: { dot: "bg-rose-500", label: "Backend offline" },
  }[state];

  return (
    <div className="flex items-center gap-2 text-xs text-zinc-400">
      <span
        className={`inline-block h-2 w-2 rounded-full ${config.dot} ${
          state === "online" ? "animate-pulse" : ""
        }`}
      />
      {config.label}
    </div>
  );
}
