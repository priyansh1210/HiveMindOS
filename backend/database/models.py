from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


AgentRole = Literal["hr", "sales", "finance", "support", "ops", "orchestrator"]
AgentStatus = Literal["idle", "working", "waiting", "collaborating", "paused"]
TaskStatus = Literal["pending", "planning", "in_progress", "completed", "failed"]
MessageType = Literal[
    "request", "response", "info", "escalation", "broadcast", "user", "system"
]
Priority = Literal["low", "medium", "high", "urgent"]


# ============================================================
# Company
# ============================================================
class CompanyBase(BaseModel):
    name: str
    description: Optional[str] = None
    industry: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class Company(CompanyBase):
    id: UUID
    created_at: datetime


# ============================================================
# Agent
# ============================================================
class AgentBase(BaseModel):
    name: str
    role: AgentRole
    system_prompt: str
    avatar_url: Optional[str] = None
    color: Optional[str] = None


class AgentCreate(AgentBase):
    company_id: UUID


class Agent(AgentBase):
    id: UUID
    company_id: UUID
    status: AgentStatus = "idle"
    created_at: datetime


class AgentStatusUpdate(BaseModel):
    status: AgentStatus


# ============================================================
# Task
# ============================================================
class SubTask(BaseModel):
    id: int
    description: str
    assigned_to: AgentRole
    depends_on: list[int] = Field(default_factory=list)
    priority: Priority = "medium"
    status: TaskStatus = "pending"
    result: Optional[str] = None


class TaskPlan(BaseModel):
    task_title: str
    subtasks: list[SubTask]
    execution_order: Literal["parallel", "sequential", "mixed"] = "mixed"


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None


class TaskCreate(TaskBase):
    company_id: UUID


class TaskUserInput(BaseModel):
    """User-facing task submission — single prompt, company resolved server-side."""
    prompt: str
    company_id: Optional[UUID] = None


class Task(TaskBase):
    id: UUID
    company_id: UUID
    status: TaskStatus
    created_by: str
    assigned_agents: list[str] = Field(default_factory=list)
    plan: Optional[dict[str, Any]] = None
    result: Optional[dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# ============================================================
# Message (agent-to-agent)
# ============================================================
class MessageBase(BaseModel):
    from_agent: str
    to_agent: str
    message_type: MessageType
    content: str
    data: Optional[dict[str, Any]] = None
    priority: Priority = "medium"


class MessageCreate(MessageBase):
    task_id: UUID


class Message(MessageBase):
    id: UUID
    task_id: UUID
    created_at: datetime


# ============================================================
# Knowledge
# ============================================================
class KnowledgeBase(BaseModel):
    category: Optional[str] = None
    title: str
    content: str


class KnowledgeCreate(KnowledgeBase):
    company_id: UUID


class Knowledge(KnowledgeBase):
    id: UUID
    company_id: UUID
    created_at: datetime


# ============================================================
# Activity Log
# ============================================================
class ActivityLogCreate(BaseModel):
    agent_id: UUID
    task_id: Optional[UUID] = None
    action: str
    details: Optional[dict[str, Any]] = None
    tokens_used: int = 0
    duration_ms: int = 0


class ActivityLog(ActivityLogCreate):
    id: UUID
    created_at: datetime


# ============================================================
# Analytics
# ============================================================
class AgentPerformance(BaseModel):
    agent_id: UUID
    agent_name: str
    role: AgentRole
    tasks_completed: int
    messages_sent: int
    avg_duration_ms: float
    total_tokens: int


class TaskMetrics(BaseModel):
    total_tasks: int
    pending: int
    in_progress: int
    completed: int
    failed: int
    completion_rate: float
