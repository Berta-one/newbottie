from typing import List

class PolicyEngine:
    """Very small allow/deny checker for strings.

    You would replace this with something like OpenAI policy or Cedar.  The
    showcase here is deliberately tiny.
    """

    def __init__(self, blocked_keywords: List[str] | None = None):
        default = ["delete all", "drop database", "shutdown", "rm -rf /"]
        self.blocked_keywords = set(blocked_keywords or default)

    def allowed(self, command: str) -> bool:
        lowered = command.lower()
        return not any(keyword in lowered for keyword in self.blocked_keywords)

    def assert_allowed(self, command: str):
        if not self.allowed(command):
            raise PermissionError("⛔ Action blocked by policy engine")