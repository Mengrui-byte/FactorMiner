"""Knowledge providers used by the recursive RSI agent."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol


class KnowledgeProvider(Protocol):
    def search(self, query: str, *, limit: int = 5) -> list[dict[str, Any]]: ...

    def novelty(self, statement: str) -> dict[str, Any]: ...


@dataclass
class LocalKnowledge:
    """Deterministic fallback when DigitalScholar is not available."""

    entries: list[dict[str, Any]]

    def search(self, query: str, *, limit: int = 5) -> list[dict[str, Any]]:
        terms = {part.lower() for part in query.split() if part}
        scored = []
        for entry in self.entries:
            text = json.dumps(entry, ensure_ascii=False).lower()
            scored.append((sum(term in text for term in terms), entry))
        return [entry for score, entry in sorted(scored, key=lambda item: item[0], reverse=True)[:limit] if score]

    def novelty(self, statement: str) -> dict[str, Any]:
        matches = self.search(statement, limit=3)
        return {"status": "PARTIALLY-KNOWN" if matches else "NOVEL", "matches": matches}
