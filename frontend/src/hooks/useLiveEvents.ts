"use client";

import { useEffect, useRef, useState } from "react";
import { wsUrl } from "@/lib/api";
import type { AgentRole, AgentStatus, Message, TaskStatus } from "@/lib/types";

export type LiveConnectionState = "connecting" | "open" | "closed";

export interface AgentStatusEvent {
  role: AgentRole;
  status: AgentStatus;
}

export interface TaskStatusEvent {
  task_id: string;
  status: TaskStatus;
  plan?: unknown;
  result?: unknown;
  completed_at?: string;
}

type ServerEvent =
  | { type: "connected"; data: { ok: boolean } }
  | { type: "message"; data: Message }
  | { type: "task_status"; data: TaskStatusEvent }
  | { type: "agent_status"; data: AgentStatusEvent };

export interface UseLiveEventsResult {
  connection: LiveConnectionState;
  messages: Message[];
  agentStatus: Partial<Record<AgentRole, AgentStatus>>;
  taskStatus: Record<string, TaskStatusEvent>;
}

export function useLiveEvents(initialMessages: Message[] = []): UseLiveEventsResult {
  const [connection, setConnection] = useState<LiveConnectionState>("connecting");
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [agentStatus, setAgentStatus] = useState<
    Partial<Record<AgentRole, AgentStatus>>
  >({});
  const [taskStatus, setTaskStatus] = useState<Record<string, TaskStatusEvent>>({});

  const seenMessageIds = useRef<Set<string>>(new Set(initialMessages.map((m) => m.id)));
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closedByUs = useRef(false);

  useEffect(() => {
    closedByUs.current = false;

    const connect = () => {
      setConnection("connecting");
      let ws: WebSocket;
      try {
        ws = new WebSocket(wsUrl());
      } catch {
        scheduleReconnect();
        return;
      }
      wsRef.current = ws;

      ws.onopen = () => setConnection("open");

      ws.onmessage = (ev) => {
        let parsed: ServerEvent;
        try {
          parsed = JSON.parse(ev.data) as ServerEvent;
        } catch {
          return;
        }
        switch (parsed.type) {
          case "connected":
            break;
          case "message": {
            const msg = parsed.data;
            if (seenMessageIds.current.has(msg.id)) return;
            seenMessageIds.current.add(msg.id);
            setMessages((prev) => [...prev, msg]);
            break;
          }
          case "agent_status":
            setAgentStatus((prev) => ({
              ...prev,
              [parsed.data.role]: parsed.data.status,
            }));
            break;
          case "task_status":
            setTaskStatus((prev) => ({
              ...prev,
              [parsed.data.task_id]: parsed.data,
            }));
            break;
        }
      };

      ws.onclose = () => {
        setConnection("closed");
        if (!closedByUs.current) scheduleReconnect();
      };

      ws.onerror = () => {
        try {
          ws.close();
        } catch {
          /* noop */
        }
      };
    };

    const scheduleReconnect = () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      reconnectTimer.current = setTimeout(connect, 2000);
    };

    connect();

    return () => {
      closedByUs.current = true;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      const ws = wsRef.current;
      if (ws && ws.readyState <= WebSocket.OPEN) ws.close();
    };
  }, []);

  return { connection, messages, agentStatus, taskStatus };
}
