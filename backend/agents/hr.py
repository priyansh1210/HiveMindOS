from .base import BaseAgent
from .tools.hr_tools import build_hr_tools


class HRAgent(BaseAgent):
    role = "hr"
    name = "HR Agent"
    color = "#a78bfa"

    def __init__(self, company_context: str = "") -> None:
        super().__init__(company_context=company_context, tools=build_hr_tools())

    def base_system_prompt(self) -> str:
        return (
            "You are the HR Agent. You are professional, empathetic, and "
            "policy-focused. You handle hiring, onboarding, employee questions, "
            "and policy lookups. You are concise and human."
        )
