"""BaseAgent — reasoning loop with text-based tool calling.

Protocol
--------
The LLM is told it may either:
  (a) Emit one or more tool calls as fenced JSON blocks:
        ```tool_call
        {"name": "estimate_budget", "args": {"project": "summer campaign"}}
        ```
      Tool results are appended to the conversation and the agent loops.
  (b) Emit a final natural-language response (no tool_call blocks).
      That terminates the turn.

The agent may also reference peers via `→ @agent_name: ...` lines — these are
inert to the agent itself but are parsed by the Orchestrator (Day 3) to drive
agent-to-agent delegation.

Memory is a per-agent conversation history (list of role/content dicts) that
persists across invocations until `reset()` is called.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from llm_client import Role as LLMRole
from llm_client import call_llm

from .tools.base import ToolRegistry


TOOL_CALL_PATTERN = re.compile(r"```tool_call\s*(.*?)\s*```", re.DOTALL)
AGENT_MENTION_PATTERN = re.compile(r"→\s*@(\w+)\s*:\s*(.+)")

DEFAULT_MAX_TURNS = 4


@dataclass
class ToolInvocation:
    name: str
    args: dict[str, Any]
    result: Any = None
    error: Optional[str] = None
    duration_ms: int = 0


@dataclass
class AgentMention:
    to_agent: str
    content: str


@dataclass
class AgentRun:
    """Result of a single agent.run() call."""

    response: str
    tool_calls: list[ToolInvocation] = field(default_factory=list)
    mentions: list[AgentMention] = field(default_factory=list)
    turns: int = 0
    total_duration_ms: int = 0


class BaseAgent:
    """Specialized agents subclass this and set role/name/system_prompt/tools."""

    role: str = "base"
    name: str = "Base Agent"
    color: str = "#94a3b8"
    llm_role: LLMRole = "agent"  # "agent" (Flash) by default; orchestrator overrides

    def __init__(
        self,
        company_context: Optional[str] = None,
        tools: Optional[ToolRegistry] = None,
        max_turns: int = DEFAULT_MAX_TURNS,
    ) -> None:
        self.company_context = company_context or ""
        self.tools = tools or ToolRegistry()
        self.max_turns = max_turns
        self.memory: list[dict[str, str]] = []

    # ----------------------------------------------------------------
    # Subclass hooks
    # ----------------------------------------------------------------
    def base_system_prompt(self) -> str:
        """Override in subclasses with the agent's identity + role."""
        return f"You are {self.name}."

    # ----------------------------------------------------------------
    # System prompt assembly
    # ----------------------------------------------------------------
    def _full_system_prompt(self, inbox: list[str]) -> str:
        sections = [self.base_system_prompt()]

        if self.company_context:
            sections.append(f"\nCOMPANY CONTEXT:\n{self.company_context}")

        if inbox:
            inbox_str = "\n".join(f"- {m}" for m in inbox)
            sections.append(f"\nMESSAGES FROM OTHER AGENTS:\n{inbox_str}")

        sections.append(
            "\nAVAILABLE TOOLS:\n"
            f"{self.tools.render()}\n"
            "\nHOW TO USE TOOLS\n"
            "If a tool would help, emit a fenced block like:\n"
            "```tool_call\n"
            '{"name": "<tool_name>", "args": {"<arg>": "<value>"}}\n'
            "```\n"
            "You may emit multiple tool_call blocks in one response. After "
            "tools run, you'll be called again with their results and can "
            "either call more tools or give a final answer.\n"
            "\nHOW TO COLLABORATE\n"
            "If you need help from another agent, include a line:\n"
            "→ @<agent_role>: <what you need>\n"
            "Available roles: hr, sales, finance, support, ops.\n"
            "\nHOW TO FINISH\n"
            "When you have your answer, respond in plain text with no "
            "tool_call blocks. Be concise — 2-4 sentences typical.\n"
        )

        return "\n".join(sections)

    # ----------------------------------------------------------------
    # Memory
    # ----------------------------------------------------------------
    def reset(self) -> None:
        self.memory.clear()

    def remember(self, role: str, content: str) -> None:
        self.memory.append({"role": role, "content": content})

    def _render_memory(self) -> str:
        if not self.memory:
            return ""
        lines = []
        for entry in self.memory:
            lines.append(f"[{entry['role']}] {entry['content']}")
        return "\n".join(lines)

    # ----------------------------------------------------------------
    # Main loop
    # ----------------------------------------------------------------
    async def run(
        self,
        prompt: str,
        inbox: Optional[list[str]] = None,
    ) -> AgentRun:
        """Run a single user/peer prompt through the agent's reasoning loop."""
        start = time.perf_counter()
        run = AgentRun(response="")
        inbox = inbox or []

        self.remember("user", prompt)
        system_prompt = self._full_system_prompt(inbox)

        for turn in range(1, self.max_turns + 1):
            run.turns = turn

            # Build the per-turn user prompt = conversation so far.
            conversation = self._render_memory()
            llm_response = await call_llm(
                prompt=conversation,
                system_prompt=system_prompt,
                role=self.llm_role,
                temperature=0.6,
                max_tokens=1024,
            )
            self.remember("assistant", llm_response)

            tool_calls = self._parse_tool_calls(llm_response)
            if not tool_calls:
                run.response = self._strip_directives(llm_response)
                run.mentions = self._parse_mentions(llm_response)
                break

            # Execute every requested tool, append results to memory, loop.
            for call in tool_calls:
                invocation = await self._execute_tool(call)
                run.tool_calls.append(invocation)
                payload = {
                    "tool": invocation.name,
                    "result": invocation.result,
                    "error": invocation.error,
                }
                self.remember("tool", json.dumps(payload, default=str))
        else:
            # Hit max_turns without a final response — surface what we have.
            run.response = (
                "I hit my reasoning-step limit before producing a final answer."
            )

        run.total_duration_ms = int((time.perf_counter() - start) * 1000)
        return run

    # ----------------------------------------------------------------
    # Parsing helpers
    # ----------------------------------------------------------------
    @staticmethod
    def _parse_tool_calls(text: str) -> list[dict[str, Any]]:
        calls: list[dict[str, Any]] = []
        for raw in TOOL_CALL_PATTERN.findall(text):
            try:
                obj = json.loads(raw)
                if isinstance(obj, dict) and "name" in obj:
                    obj.setdefault("args", {})
                    calls.append(obj)
            except json.JSONDecodeError:
                continue
        return calls

    @staticmethod
    def _parse_mentions(text: str) -> list[AgentMention]:
        return [
            AgentMention(to_agent=m.group(1).lower(), content=m.group(2).strip())
            for m in AGENT_MENTION_PATTERN.finditer(text)
        ]

    @staticmethod
    def _strip_directives(text: str) -> str:
        cleaned = TOOL_CALL_PATTERN.sub("", text)
        cleaned = AGENT_MENTION_PATTERN.sub("", cleaned)
        return cleaned.strip()

    async def _execute_tool(self, call: dict[str, Any]) -> ToolInvocation:
        name = call.get("name", "")
        args = call.get("args", {}) or {}
        invocation = ToolInvocation(name=name, args=args)

        tool = self.tools.get(name)
        if tool is None:
            invocation.error = f"Unknown tool: {name}"
            return invocation

        start = time.perf_counter()
        try:
            invocation.result = await tool.call(**args)
        except TypeError as exc:
            invocation.error = f"Bad arguments for {name}: {exc}"
        except Exception as exc:  # noqa: BLE001 — surface any tool failure
            invocation.error = f"{type(exc).__name__}: {exc}"
        finally:
            invocation.duration_ms = int((time.perf_counter() - start) * 1000)
        return invocation
