from .base import BaseAgent
from .tools.support_tools import build_support_tools


class SupportAgent(BaseAgent):
    role = "support"
    name = "Support Agent"
    color = "#60a5fa"

    def __init__(self, company_context: str = "") -> None:
        super().__init__(company_context=company_context, tools=build_support_tools())

    def base_system_prompt(self) -> str:
        return (
            "You are the Customer Support Agent. You are friendly, patient, "
            "and solution-oriented. You handle complaints, ticket routing, "
            "FAQ responses, and escalations. You lead with empathy and end "
            "with a clear next step."
        )
