from .memory import MemoryStore
from typing import Any, Dict

class Reflector:
    """Light-weight self-evaluation helper.

    Stores a short summary of every action + outcome so the agent can learn
    from past mistakes.  A proper implementation would call an LLM to score the
    quality of the step; here we rely on a very naive success heuristic.
    """

    def __init__(self, memory: MemoryStore):
        self.memory = memory

    def reflect(self, action: str, outcome: str, metadata: Dict[str, Any] | None = None):
        success = "error" not in outcome.lower()
        record = {
            "action": action,
            "outcome": outcome[:256],  # truncate to save space
            "success": success,
        }
        if metadata:
            record["meta"] = metadata
        self.memory.add("reflection", record)
        return success