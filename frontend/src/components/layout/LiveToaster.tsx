"use client";

import { useEffect, useRef } from "react";
import { useLiveEvents } from "@/hooks/useLiveEvents";
import { useToast } from "@/lib/toast";
import { api } from "@/lib/api";

export function LiveToaster() {
  const { taskStatus } = useLiveEvents([]);
  const { toast } = useToast();
  const seenTransitions = useRef<Set<string>>(new Set());
  const titleCache = useRef<Map<string, string>>(new Map());

  useEffect(() => {
    for (const [taskId, ev] of Object.entries(taskStatus)) {
      const key = `${taskId}:${ev.status}`;
      if (seenTransitions.current.has(key)) continue;
      seenTransitions.current.add(key);

      const fire = (title: string) => {
        if (ev.status === "completed") {
          toast({
            title: "Task completed",
            description: title,
            variant: "success",
          });
        } else if (ev.status === "failed") {
          toast({
            title: "Task failed",
            description: title,
            variant: "error",
          });
        } else if (ev.status === "in_progress") {
          toast({
            title: "Agents dispatched",
            description: title,
            variant: "info",
            duration: 2500,
          });
        }
      };

      if (ev.status !== "completed" && ev.status !== "failed" && ev.status !== "in_progress") {
        continue;
      }

      const cached = titleCache.current.get(taskId);
      if (cached) {
        fire(cached);
      } else {
        api
          .getTask(taskId)
          .then((t) => {
            titleCache.current.set(taskId, t.title);
            fire(t.title);
          })
          .catch(() => fire(`task ${taskId.slice(0, 8)}`));
      }
    }
  }, [taskStatus, toast]);

  return null;
}
