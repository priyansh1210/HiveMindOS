from .base import ToolRegistry, tool
from ._helpers import llm_tool


@tool(
    name="search_employees",
    description="Look up employees matching a query (role, team, skill).",
    args={"query": {"type": "str", "description": "Search criteria, e.g. 'senior designer'"}},
)
async def search_employees(query: str) -> dict:
    return await llm_tool(
        system="You are an HR records assistant. Return 2-4 plausible employee "
        "matches as a short bulleted list (name, role, team, tenure).",
        user=f"Find employees matching: {query}",
        max_tokens=400,
    )


@tool(
    name="draft_job_posting",
    description="Draft a job posting for an open role.",
    args={
        "role": {"type": "str", "description": "Role title, e.g. 'Senior Frontend Engineer'"},
        "team": {"type": "str", "description": "Team or department name"},
    },
)
async def draft_job_posting(role: str, team: str) -> dict:
    return await llm_tool(
        system="You are a recruiter. Write a concise job posting with sections: "
        "About, Responsibilities (4 bullets), Requirements (4 bullets), Nice-to-haves (2).",
        user=f"Role: {role}. Team: {team}.",
        max_tokens=550,
    )


@tool(
    name="schedule_interview",
    description="Propose an interview slot for a candidate.",
    args={
        "candidate": {"type": "str", "description": "Candidate name"},
        "role": {"type": "str", "description": "Role they're interviewing for"},
    },
)
async def schedule_interview(candidate: str, role: str) -> dict:
    return await llm_tool(
        system="You are a scheduling assistant. Propose 3 interview slots in "
        "the next 7 business days and the interview panel composition.",
        user=f"Candidate: {candidate}. Role: {role}.",
        max_tokens=300,
    )


@tool(
    name="analyze_resume",
    description="Analyze a resume snippet for strengths and concerns.",
    args={"resume_summary": {"type": "str", "description": "A short summary of the candidate"}},
)
async def analyze_resume(resume_summary: str) -> dict:
    return await llm_tool(
        system="You are a hiring manager. Output: Strengths (3 bullets), "
        "Concerns (2 bullets), Recommendation (1 line).",
        user=resume_summary,
        max_tokens=400,
    )


@tool(
    name="generate_onboarding_plan",
    description="Generate a 30/60/90-day onboarding plan for a new hire.",
    args={
        "role": {"type": "str", "description": "New hire role"},
        "team": {"type": "str", "description": "Team they're joining"},
    },
)
async def generate_onboarding_plan(role: str, team: str) -> dict:
    return await llm_tool(
        system="You are an HR onboarding lead. Output a 30/60/90 plan with "
        "3 milestones per phase. Be specific to the role.",
        user=f"Role: {role}. Team: {team}.",
        max_tokens=600,
    )


def build_hr_tools() -> ToolRegistry:
    registry = ToolRegistry()
    for t in (
        search_employees,
        draft_job_posting,
        schedule_interview,
        analyze_resume,
        generate_onboarding_plan,
    ):
        registry.register(t)
    return registry
