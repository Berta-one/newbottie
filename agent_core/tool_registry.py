from typing import Callable, Dict, Any

class ToolRegistry:
    """In-memory registry for external capabilities."""

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register_tool(
        self,
        name: str,
        func: Callable[..., Any],
        description: str = "",
        cost: float = 0.0,
    ):
        if name in self._tools:
            raise ValueError(f"Tool '{name}' already registered")
        self._tools[name] = {
            "func": func,
            "description": description,
            "cost": cost,
        }

    def list_tools(self):
        return {k: v["description"] for k, v in self._tools.items()}

    def call(self, name: str, **kwargs):
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry")
        return self._tools[name]["func"](**kwargs)