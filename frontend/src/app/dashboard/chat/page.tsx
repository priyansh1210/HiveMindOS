import { api } from "@/lib/api";
import type { Agent, Message } from "@/lib/types";
import { ChatFeed } from "@/components/chat/ChatFeed";

const RECENT_LIMIT = 50;

export default async function ChatPage() {
  let agents: Agent[] = [];
  let messages: Message[] = [];
  let error: string | null = null;

  try {
    const [a, m] = await Promise.all([api.listAgents(), api.listMessages()]);
    agents = a;
    messages = m
      .slice()
      .sort(
        (x, y) =>
          new Date(x.created_at).getTime() - new Date(y.created_at).getTime(),
      )
      .slice(-RECENT_LIMIT);
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to load chat data";
  }

  if (error) {
    return (
      <div className="rounded-xl border border-rose-900/50 bg-rose-950/20 p-6 text-sm text-rose-300">
        <div className="font-semibold mb-1">Couldn&apos;t load chat data</div>
        <div className="text-xs text-rose-400/80 font-mono">{error}</div>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-5xl flex flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold text-zinc-100">Agent Chat</h2>
        <p className="text-xs text-zinc-500">
          Every message your agents send each other, live.
        </p>
      </div>
      <ChatFeed agents={agents} initialMessages={messages} />
    </div>
  );
}
