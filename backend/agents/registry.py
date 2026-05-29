"""Singleton registry of live agent instances, keyed by role."""

from __future__ import annotations

from functools import lru_cache

from .base import BaseAgent
from .finance import FinanceAgent
from .hr import HRAgent
from .ops import OpsAgent
from .sales import SalesAgent
from .support import SupportAgent


DEFAULT_COMPANY_CONTEXT = (
    "Company: NovaTech Inc.\n"
    "Industry: SaaS — AI-powered productivity tools for modern teams.\n"
    "Flagship product: NovaSync Pro — smart scheduling, automated meeting "
    "notes, cross-team project sync. $49/user/month."
)


class AgentRegistry:
    def __init__(self, company_context: str = DEFAULT_COMPANY_CONTEXT) -> None:
        self._agents: dict[str, BaseAgent] = {
            "hr": HRAgent(company_context=company_context),
            "sales": SalesAgent(company_context=company_context),
            "finance": FinanceAgent(company_context=company_context),
            "support": SupportAgent(company_context=company_context),
            "ops": OpsAgent(company_context=company_context),
        }

    def get(self, role: str) -> BaseAgent | None:
        return self._agents.get(role.lower())

    def all(self) -> dict[str, BaseAgent]:
        return dict(self._agents)

    def roles(self) -> list[str]:
        return list(self._agents.keys())


@lru_cache
def get_registry() -> AgentRegistry:
    return AgentRegistry()
