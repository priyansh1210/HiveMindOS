from .base import BaseAgent
from .tools.ops_tools import build_ops_tools


class OpsAgent(BaseAgent):
    role = "ops"
    name = "Ops Agent"
    color = "#f87171"

    def __init__(self, company_context: str = "") -> None:
        super().__init__(company_context=company_context, tools=build_ops_tools())

    def base_system_prompt(self) -> str:
        return (
            "You are the Operations Agent. You are systematic, efficient, and "
            "process-focused. You handle task management, scheduling, workflow "
            "optimization, and reporting. You think in timelines, owners, and "
            "blockers."
        )
