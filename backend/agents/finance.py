from .base import BaseAgent
from .tools.finance_tools import build_finance_tools


class FinanceAgent(BaseAgent):
    role = "finance"
    name = "Finance Agent"
    color = "#fbbf24"

    def __init__(self, company_context: str = "") -> None:
        super().__init__(company_context=company_context, tools=build_finance_tools())

    def base_system_prompt(self) -> str:
        return (
            "You are the Finance Agent. You are precise, cautious, and "
            "analytical. You handle budgets, ROI, invoicing, and forecasting. "
            "You always give specific numbers and call out assumptions."
        )
