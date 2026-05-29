"""Tool registry + @tool decorator.

Tools are async Python functions an agent can call by emitting a JSON block in
its response (see backend/agents/base.py for the protocol).

Each tool registers its name, description, JSON-schema-style arg spec, and
the function itself. The BaseAgent renders the registry into a system-prompt
section so the LLM knows what's callable.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional


ToolFn = Callable[..., Awaitable[Any]]


@dataclass
class Tool:
    name: str
    description: str
    args_schema: dict[str, dict[str, str]]  # arg_name -> {"type": ..., "description": ...}
    fn: ToolFn

    def render(self) -> str:
        """Render a single-line description for the system prompt."""
        args_str = ", ".join(
            f"{name}: {spec.get('type', 'str')}"
            for name, spec in self.args_schema.items()
        )
        return f"- {self.name}({args_str}) — {self.description}"

    async def call(self, **kwargs: Any) -> Any:
        return await self.fn(**kwargs)


@dataclass
class ToolRegistry:
    tools: dict[str, Tool] = field(default_factory=dict)

    def register(self, tool: Tool) -> None:
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self.tools.get(name)

    def names(self) -> list[str]:
        return list(self.tools.keys())

    def render(self) -> str:
        if not self.tools:
            return "(no tools available)"
        return "\n".join(t.render() for t in self.tools.values())


def tool(
    name: str,
    description: str,
    args: Optional[dict[str, dict[str, str]]] = None,
) -> Callable[[ToolFn], Tool]:
    """Decorator that wraps an async function into a Tool.

    Example:
        @tool(
            name="estimate_budget",
            description="Generate a budget estimate for a project",
            args={"project": {"type": "str", "description": "Project name"}},
        )
        async def estimate_budget(project: str) -> dict: ...
    """

    def decorator(fn: ToolFn) -> Tool:
        if not inspect.iscoroutinefunction(fn):
            raise TypeError(f"Tool function '{fn.__name__}' must be async")
        return Tool(name=name, description=description, args_schema=args or {}, fn=fn)

    return decorator
