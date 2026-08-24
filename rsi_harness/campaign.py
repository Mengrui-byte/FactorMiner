"""Guarded generation ledger for recursive self-improvement."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .contracts import canonical_hash


def _hash(value: Any) -> str:
    return canonical_hash(value)


@dataclass
class CapabilityProposal:
    proposal_id: str
    kind: str
    description: str
    parent_generation: int
    status: str = "proposed"
    evidence_ids: list[str] = field(default_factory=list)
    benchmark: dict[str, Any] = field(default_factory=dict)


@dataclass
class Generation:
    number: int
    parent: int | None
    knowledge_hash: str
    dataset_hash: str
    skill_version: str
    trial_count: int = 0
    alpha_budget: float = 0.01
    alpha_spent: float = 0.0
    evidence_ids: list[str] = field(default_factory=list)
    anomalies: list[str] = field(default_factory=list)
    proposal_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    @property
    def remaining_budget(self) -> float:
        return max(0.0, self.alpha_budget - self.alpha_spent)


class RecursiveCampaign:
    """A JSON-backed ledger that makes recursive changes reviewable."""

    schema_version = 2

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.generations: list[Generation] = []
        self.proposals: dict[str, CapabilityProposal] = {}
        self.results: list[dict[str, Any]] = []
        if self.path.exists():
            self._load()

    @property
    def current(self) -> Generation | None:
        return self.generations[-1] if self.generations else None

    def _load(self) -> None:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.generations = [Generation(**item) for item in payload.get("generations", [])]
        self.proposals = {key: CapabilityProposal(**value) for key, value in payload.get("proposals", {}).items()}
        self.results = list(payload.get("results", []))

    def _save(self) -> None:
        payload = {
            "schema_version": self.schema_version,
            "campaign": "rsi-recursive",
            "generations": [asdict(item) for item in self.generations],
            "proposals": {key: asdict(value) for key, value in self.proposals.items()},
            "results": self.results,
        }
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def start(self, *, knowledge_snapshot: Any, dataset_hash: str, skill_version: str, alpha_budget: float = 0.01) -> Generation:
        if self.current is not None:
            raise ValueError("campaign already started")
        if not math.isfinite(alpha_budget) or alpha_budget < 0:
            raise ValueError("alpha_budget must be a finite non-negative number")
        generation = Generation(0, None, _hash(knowledge_snapshot), dataset_hash, skill_version, alpha_budget=float(alpha_budget))
        self.generations.append(generation)
        self._save()
        return generation

    def record_result(self, result: dict[str, Any], *, alpha_spent: float = 0.0) -> None:
        current = self.current
        if current is None:
            raise ValueError("campaign is not started")
        if alpha_spent < 0 or current.alpha_spent + alpha_spent > current.alpha_budget + 1e-12:
            raise ValueError("alpha budget exceeded")
        current.alpha_spent += float(alpha_spent)
        self.results.append(result)
        evidence_id = result.get("evidence_id")
        if evidence_id and evidence_id not in current.evidence_ids:
            current.evidence_ids.append(evidence_id)
        current.trial_count += 1
        self._save()

    def ensure_budget(self, amount: float) -> None:
        """Reject a batch before computation if its planned alpha cost is too high."""

        current = self.current
        if current is None:
            raise ValueError("campaign is not started")
        if not math.isfinite(amount) or amount < 0 or current.alpha_spent + amount > current.alpha_budget + 1e-12:
            raise ValueError(
                f"alpha budget exceeded: requested={amount:.12g}, "
                f"remaining={current.remaining_budget:.12g}"
            )

    def propose(self, *, kind: str, description: str, evidence_ids: list[str] | None = None) -> CapabilityProposal:
        current = self.current
        if current is None:
            raise ValueError("campaign is not started")
        seed = {"generation": current.number, "kind": kind, "description": description, "evidence_ids": evidence_ids or []}
        proposal = CapabilityProposal("cap-" + _hash(seed)[:16], kind, description, current.number, evidence_ids=list(evidence_ids or []))
        self.proposals[proposal.proposal_id] = proposal
        current.proposal_ids.append(proposal.proposal_id)
        self._save()
        return proposal

    def benchmark(self, proposal_id: str, *, parent_score: float, candidate_score: float, checks: dict[str, bool]) -> CapabilityProposal:
        proposal = self.proposals[proposal_id]
        proposal.status = "validated" if all(checks.values()) and candidate_score > parent_score else "rejected"
        proposal.benchmark = {"parent_score": parent_score, "candidate_score": candidate_score, "checks": checks, "improvement": candidate_score - parent_score}
        self._save()
        return proposal

    def advance(self, *, knowledge_snapshot: Any, dataset_hash: str, skill_version: str, anomalies: list[str] | None = None) -> Generation:
        parent = self.current
        if parent is None:
            raise ValueError("campaign is not started")
        generation = Generation(parent.number + 1, parent.number, _hash(knowledge_snapshot), dataset_hash, skill_version, alpha_budget=parent.alpha_budget, alpha_spent=parent.alpha_spent, anomalies=list(anomalies or []))
        self.generations.append(generation)
        self._save()
        return generation

    def summary(self) -> dict[str, Any]:
        current = self.current
        return {
            "campaign": "rsi-recursive",
            "generation": current.number if current else None,
            "trials": current.trial_count if current else 0,
            "remaining_alpha_budget": current.remaining_budget if current else None,
            "anomalies": current.anomalies if current else [],
            "proposals": {key: asdict(value) for key, value in self.proposals.items()},
        }
