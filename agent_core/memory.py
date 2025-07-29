import json
import os
from datetime import datetime
from typing import List, Dict, Any
import difflib

class MemoryStore:
    """Durable append-only JSONL memory.

    Uses a plain *memory.jsonl* file so it works in constrained environments
    without additional dependencies.  Each line is a valid JSON object with a
    timestamp and arbitrary payload.
    """

    def __init__(self, path: str = "memory.jsonl", max_events: int = 10_000):
        self.path = path
        self.max_events = max_events
        self._events: List[Dict[str, Any]] = []
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add(self, event_type: str, payload: Dict[str, Any]):
        """Append a new event to the store."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "payload": payload,
        }
        self._events.append(event)
        # Keep only the most recent *max_events* in memory
        if len(self._events) > self.max_events:
            self._events = self._events[-self.max_events :]
        self._persist(event)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Very simple similarity search using SequenceMatcher.

        In production you would replace this with a vector store or embedding
        database (e.g. FAISS, Chroma, Weaviate).  This naive version keeps the
        footprint small and dependency-free.
        """
        scored = []
        for ev in self._events:
            corpus = json.dumps(ev)
            score = difflib.SequenceMatcher(None, query, corpus).ratio()
            scored.append((score, ev))
        scored.sort(key=lambda s: s[0], reverse=True)
        return [ev for _, ev in scored[:top_k]]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        self._events.append(json.loads(line))
                    except json.JSONDecodeError:
                        # Skip malformed lines (safety)
                        continue

    def _persist(self, event: Dict[str, Any]):
        """Append the latest event and, if we trimmed, rewrite the file."""
        if len(self._events) == self.max_events:
            # Re-write full file to prune old events
            with open(self.path, "w", encoding="utf-8") as f:
                for ev in self._events:
                    f.write(json.dumps(ev) + "\n")
        else:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")