from typing import List, Dict
import uuid
from .memory import MemoryStore

class Planner:
    """Simple objective decomposer.

    Splits an objective string into subtasks using basic heuristics.  In real
    systems you might plug in an LLM or specialised planner, but this keeps the
    footprint small while still demonstrating the interface.
    """

    def __init__(self, memory: MemoryStore):
        self.memory = memory

    def create_plan(self, objective: str) -> List[Dict[str, str]]:
        # Naive split on conjunctions / commas
        separators = [" and ", ",", ";", " then "]
        segments = [objective]
        for sep in separators:
            tmp = []
            for s in segments:
                tmp.extend([p.strip() for p in s.split(sep) if p.strip()])
            segments = tmp
        plan = [
            {"id": str(uuid.uuid4())[:8], "task": seg, "status": "pending"}
            for seg in segments
        ]
        self.memory.add("plan_created", {"objective": objective, "plan": plan})
        return plan

    def mark_task(self, task_id: str, status: str):
        """Update the status of a task and persist."""
        assert status in {"pending", "in_progress", "completed", "cancelled"}
        self.memory.add("task_update", {"task_id": task_id, "status": status})