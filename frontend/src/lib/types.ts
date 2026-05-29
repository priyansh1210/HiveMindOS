export type AgentRole = "hr" | "sales" | "finance" | "support" | "ops";

export type AgentStatus = "idle" | "working" | "collaborating" | "waiting";

export interface Agent {
  id: string;
  company_id: string;
  name: string;
  role: AgentRole;
  system_prompt: string;
  status: AgentStatus;
  color: string;
  avatar_url: string | null;
  created_at: string;
}

export type TaskStatus = "pending" | "in_progress" | "completed" | "failed";

export interface Subtask {
  id: number;
  description: string;
  assigned_to: AgentRole;
  depends_on: number[];
  priority: "low" | "medium" | "high" | "urgent";
  status: "pending" | "in_progress" | "completed" | "failed";
  result: string | null;
}

export interface TaskPlan {
  subtasks: Subtask[];
  execution_order?: "parallel" | "sequential" | "mixed";
}

export interface TaskResult {
  task_title?: string;
  summary?: string;
  subtask_count?: number;
  error?: string | null;
}

export interface Task {
  id: string;
  company_id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  created_by: string;
  assigned_agents: string[];
  plan: TaskPlan | null;
  result: TaskResult | null;
  created_at: string;
  completed_at: string | null;
}

export type MessageType =
  | "request"
  | "response"
  | "info"
  | "escalation"
  | "broadcast"
  | "user";

export interface Message {
  id: string;
  task_id: string | null;
  from_agent: string;
  to_agent: string;
  message_type: MessageType;
  content: string;
  data: Record<string, unknown> | null;
  priority: "low" | "medium" | "high" | "urgent";
  created_at: string;
}

export interface TaskMetrics {
  total_tasks: number;
  pending: number;
  in_progress: number;
  completed: number;
  failed: number;
  completion_rate: number;
}

export interface AgentMetric {
  agent_id: string;
  agent_name: string;
  role: AgentRole;
  color: string | null;
  messages_sent: number;
  tasks_touched: number;
}
