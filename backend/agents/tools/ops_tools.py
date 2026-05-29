from .base import ToolRegistry, tool
from ._helpers import llm_tool


@tool(
    name="create_task",
    description="Create a new task with owner and deadline.",
    args={
        "title": {"type": "str", "description": "Task title"},
        "owner": {"type": "str", "description": "Owner role or person"},
        "deadline": {"type": "str", "description": "Deadline / due date"},
    },
)
async def create_task(title: str, owner: str, deadline: str) -> dict:
    return await llm_tool(
        system="You are a project manager. Return a task record: id (TSK-xxxx), "
        "title, owner, deadline, status (open), 2-3 acceptance criteria.",
        user=f"Title: {title}. Owner: {owner}. Deadline: {deadline}",
        max_tokens=300,
    )


@tool(
    name="assign_task",
    description="Assign an existing task to a specific person/team.",
    args={
        "task_id": {"type": "str", "description": "Task ID"},
        "assignee": {"type": "str", "description": "Who you're assigning to"},
    },
)
async def assign_task(task_id: str, assignee: str) -> dict:
    return await llm_tool(
        system="You are a project manager. Confirm the assignment with: task id, "
        "assignee, brief context for the assignee, expected check-in cadence.",
        user=f"Task: {task_id}. Assignee: {assignee}",
        max_tokens=250,
    )


@tool(
    name="track_progress",
    description="Summarize progress on a project or workstream.",
    args={"project": {"type": "str", "description": "Project name"}},
)
async def track_progress(project: str) -> dict:
    return await llm_tool(
        system="You are a project manager. Output: % complete, on/at-risk/behind, "
        "top 3 in-flight tasks, top 1 blocker, next milestone.",
        user=f"Project: {project}",
        max_tokens=350,
    )


@tool(
    name="schedule_meeting",
    description="Schedule a meeting with attendees and an agenda.",
    args={
        "topic": {"type": "str", "description": "Meeting topic"},
        "attendees": {"type": "str", "description": "Attendees (free-form)"},
    },
)
async def schedule_meeting(topic: str, attendees: str) -> dict:
    return await llm_tool(
        system="You are an EA. Output: proposed time (within next 5 business "
        "days), duration, attendees, 3-point agenda, prep notes.",
        user=f"Topic: {topic}. Attendees: {attendees}",
        max_tokens=300,
    )


@tool(
    name="generate_report",
    description="Generate a short status report for a workstream.",
    args={
        "topic": {"type": "str", "description": "Report topic"},
        "period": {"type": "str", "description": "Reporting period"},
    },
)
async def generate_report(topic: str, period: str) -> dict:
    return await llm_tool(
        system="You are a project manager. Output a status report: Summary "
        "(2 lines), Wins (3 bullets), Risks (2), Next steps (3).",
        user=f"Topic: {topic}. Period: {period}",
        max_tokens=450,
    )


def build_ops_tools() -> ToolRegistry:
    registry = ToolRegistry()
    for t in (
        create_task,
        assign_task,
        track_progress,
        schedule_meeting,
        generate_report,
    ):
        registry.register(t)
    return registry
