"""Guarded recursive research state for domain-specific agent campaigns.

The campaign is intentionally a state ledger, not an autonomous code writer. An
agent may propose a capability change, but the change is only promoted after a
deterministic benchmark records an improvement over the parent generation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


@dataclass
class CapabilityProposal:
    proposal_id: str
    kind: str
    description: str
    parent_generation: int
    evidence_ids: list[str] = field(default_factory=list)
    status: str = "proposed"
    benchmark: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)


@dataclass
class Generation:
    generation: int
    parent_generation: int | None
    knowledge_snapshot_hash: str
    operator_registry_hash: str
    skill_version: str
    dataset_hash: str
    trial_count: int = 0
    alpha_budget_total: float = 0.01
    alpha_budget_remaining: float = 0.01
    result_ids: list[str] = field(default_factory=list)
    anomalies: list[str] = field(default_factory=list)
    capability_proposals: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)


class RecursiveCampaign:
    """Persist generation state and enforce monotone, benchmarked evolution."""

    SCHEMA_VERSION = 1

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.generations: list[Generation] = []
        self.proposals: dict[str, CapabilityProposal] = {}
        self._load()

    @property
    def current(self) -> Generation | None:
        return self.generations[-1] if self.generations else None

    def _load(self) -> None:
        if not self.path.exists():
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.generations = [Generation(**item) for item in payload.get("generations", [])]
        self.proposals = {
            key: CapabilityProposal(**value)
            for key, value in payload.get("proposals", {}).items()
        }

    def _save(self) -> None:
        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "campaign": "rsi-recursive",
            "generations": [asdict(item) for item in self.generations],
            "proposals": {key: asdict(value) for key, value in self.proposals.items()},
        }
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def start(self, *, knowledge_snapshot: Any, operator_registry: Any,
              skill_version: str, dataset_hash: str,
              alpha_budget: float = 0.01) -> Generation:
        if self.current is not None:
            raise ValueError("campaign already started; use next_generation")
        generation = Generation(
            generation=0,
            parent_generation=None,
            knowledge_snapshot_hash=_canonical_hash(knowledge_snapshot),
            operator_registry_hash=_canonical_hash(operator_registry),
            skill_version=skill_version,
            dataset_hash=dataset_hash,
            alpha_budget_total=float(alpha_budget),
            alpha_budget_remaining=float(alpha_budget),
        )
        self.generations.append(generation)
        self._save()
        return generation

    def next_generation(self, *, knowledge_snapshot: Any, operator_registry: Any,
                        skill_version: str, dataset_hash: str,
                        trial_count: int, alpha_spent: float,
                        result_ids: list[str] | None = None,
                        anomalies: list[str] | None = None) -> Generation:
        parent = self.current
        if parent is None:
            raise ValueError("campaign is not started")
        spent = float(alpha_spent)
        remaining = parent.alpha_budget_remaining - spent
        if spent < 0 or remaining < -1e-12:
            raise ValueError("alpha budget exceeded")
        generation = Generation(
            generation=parent.generation + 1,
            parent_generation=parent.generation,
            knowledge_snapshot_hash=_canonical_hash(knowledge_snapshot),
            operator_registry_hash=_canonical_hash(operator_registry),
            skill_version=skill_version,
            dataset_hash=dataset_hash,
            trial_count=int(trial_count),
            alpha_budget_total=parent.alpha_budget_total,
            alpha_budget_remaining=max(0.0, remaining),
            result_ids=list(result_ids or []),
            anomalies=list(anomalies or []),
        )
        self.generations.append(generation)
        self._save()
        return generation

    def propose_capability(self, *, kind: str, description: str,
                           evidence_ids: list[str] | None = None) -> CapabilityProposal:
        current = self.current
        if current is None:
            raise ValueError("campaign is not started")
        seed = {
            "generation": current.generation,
            "kind": kind,
            "description": description,
            "evidence_ids": evidence_ids or [],
        }
        proposal_id = "cap-" + _canonical_hash(seed)[:16]
        proposal = CapabilityProposal(
            proposal_id=proposal_id,
            kind=kind,
            description=description,
            parent_generation=current.generation,
            evidence_ids=list(evidence_ids or []),
        )
        self.proposals[proposal_id] = proposal
        current.capability_proposals.append(proposal_id)
        self._save()
        return proposal

    def benchmark_capability(self, proposal_id: str, *, parent_score: float,
                             candidate_score: float, checks: dict[str, bool]) -> CapabilityProposal:
        proposal = self.proposals[proposal_id]
        if not checks or not all(checks.values()):
            proposal.status = "rejected"
        elif candidate_score > parent_score:
            proposal.status = "validated"
        else:
            proposal.status = "rejected"
        proposal.benchmark = {
            "parent_score": float(parent_score),
            "candidate_score": float(candidate_score),
            "checks": checks,
            "improvement": float(candidate_score - parent_score),
        }
        self._save()
        return proposal

    def summary(self) -> dict[str, Any]:
        current = self.current
        return {
            "campaign": "rsi-recursive",
            "schema_version": self.SCHEMA_VERSION,
            "generation": current.generation if current else None,
            "alpha_budget_remaining": current.alpha_budget_remaining if current else None,
            "trial_count": current.trial_count if current else 0,
            "open_anomalies": current.anomalies if current else [],
            "proposals": {key: asdict(value) for key, value in self.proposals.items()},
        }


__all__ = ["CapabilityProposal", "Generation", "RecursiveCampaign"]
