"""Recursive RSI research agent with a deterministic and Harness-pluggable planner."""

from __future__ import annotations

import json
import math
import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import Any, Protocol

from .backtest import dataset_fingerprint, evaluate_hypothesis
from .campaign import RecursiveCampaign
from .contracts import ExperimentProvenance, Hypothesis, SplitSpec, canonical_hash
from .evidence import write_evidence
from .knowledge import KnowledgeProvider, LocalKnowledge


class Planner(Protocol):
    def propose(self, context: dict[str, Any]) -> list[Hypothesis]: ...


@dataclass
class RuleBasedPlanner:
    """Offline fallback planner; DeepSeek Harness can replace it through a command."""

    max_trials: int = 6

    @property
    def version(self) -> str:
        return "rule-based@1"

    def propose(self, context: dict[str, Any]) -> list[Hypothesis]:
        family = [
            Hypothesis("rsi-14-30-70", 14, 30, 70),
            Hypothesis("rsi-7-30-70", 7, 30, 70, rationale="Shorter RSI response; pre-declared family member"),
            Hypothesis("rsi-21-30-70", 21, 30, 70, rationale="Longer RSI response; pre-declared family member"),
            Hypothesis("rsi-14-20-80", 14, 20, 80, rationale="More selective extreme-zone reversal"),
            Hypothesis("rsi-14-40-60", 14, 40, 60, rationale="Higher turnover mid-zone reversal"),
            Hypothesis("rsi-28-30-70", 28, 30, 70, rationale="Slow regime-sensitive reversal"),
        ]
        return family[: self.max_trials]


class DeepSeekHarnessPlanner:
    """Call a configured Harness command using a JSON-in/JSON-out contract."""

    def __init__(self, command: str | None = None, *, fallback: Planner | None = None):
        self.command = command or os.getenv("DEEPSEEK_HARNESS_COMMAND")
        self.fallback = fallback or RuleBasedPlanner()

    def propose(self, context: dict[str, Any]) -> list[Hypothesis]:
        if not self.command:
            return self.fallback.propose(context)
        process = subprocess.run(shlex.split(self.command), input=json.dumps(context) + "\n", capture_output=True, text=True, timeout=300, check=False)
        if process.returncode:
            raise RuntimeError(process.stderr.strip() or "DeepSeek Harness planner failed")
        payload = json.loads(process.stdout)
        hypotheses = [Hypothesis(**item) for item in payload["hypotheses"]]
        if not hypotheses or len(hypotheses) > 6:
            raise ValueError("Harness must return between 1 and 6 hypotheses")
        for hypothesis in hypotheses:
            hypothesis.validate()
        return hypotheses

    @property
    def version(self) -> str:
        return "deepseek-harness@1" if self.command else "rule-based@1"


@dataclass
class RecursiveRSIAgent:
    campaign: RecursiveCampaign
    knowledge: KnowledgeProvider | None = None
    planner: Planner | None = None
    evidence_dir: str = "artifacts/evidence"

    def run_generation(self, close: list[float], split: SplitSpec, *, cost_bps: float = 5.0, skill_version: str = "rsi-agent@1", knowledge_snapshot: list[dict[str, Any]] | None = None, novelty: dict[str, Any] | None = None, alpha_cost_per_trial: float = 0.001) -> dict[str, Any]:
        provider = self.knowledge or LocalKnowledge(knowledge_snapshot or [])
        planner = self.planner or DeepSeekHarnessPlanner()
        if not math.isfinite(alpha_cost_per_trial) or alpha_cost_per_trial < 0:
            raise ValueError("alpha_cost_per_trial must be a finite non-negative number")
        data_hash = dataset_fingerprint(close)
        if self.campaign.current is None:
            snapshot = knowledge_snapshot if knowledge_snapshot is not None else provider.search("RSI time-series momentum reversal regimes", limit=5)
            self.campaign.start(knowledge_snapshot=snapshot, dataset_hash=data_hash, skill_version=skill_version)
        elif self.campaign.current.dataset_hash != data_hash:
            raise ValueError("campaign dataset hash does not match the input close series")
        snapshot = knowledge_snapshot if knowledge_snapshot is not None else provider.search("RSI momentum reversal", limit=5)
        context = {"generation": self.campaign.current.number, "knowledge": snapshot, "dataset_hash": data_hash, "split": split.__dict__, "cost_bps": cost_bps}
        novelty_result = novelty or provider.novelty("RSI threshold-conditioned reversal")
        context["novelty"] = novelty_result
        hypotheses = planner.propose(context)
        hypothesis_ids = [hypothesis.hypothesis_id for hypothesis in hypotheses]
        if len(hypothesis_ids) != len(set(hypothesis_ids)):
            raise ValueError("Harness returned duplicate hypothesis_id values")
        self.campaign.ensure_budget(len(hypotheses) * alpha_cost_per_trial)
        provenance_base = {
            "generation": self.campaign.current.number,
            "knowledge_snapshot_hash": canonical_hash(snapshot),
            "novelty_hash": canonical_hash(novelty_result),
            "skill_version": skill_version,
            "planner_version": getattr(planner, "version", planner.__class__.__name__),
            "operator_registry_hash": "rsi-wilder@1",
            "trial_family_hash": canonical_hash([hypothesis.__dict__ for hypothesis in hypotheses]),
            "selection_rule": "validation_sharpe_max_only",
            "alpha_cost_per_trial": alpha_cost_per_trial,
        }
        results = []
        for index, hypothesis in enumerate(hypotheses, start=1):
            result = evaluate_hypothesis(close, hypothesis, split, cost_bps=cost_bps, dataset_hash=data_hash, trial_index=index, provenance=ExperimentProvenance(**provenance_base))
            path = write_evidence(result, self.evidence_dir)
            self.campaign.record_result({"evidence_id": result.evidence_id, "hypothesis_id": hypothesis.hypothesis_id, "validation_sharpe": result.validation_score(), "provenance": provenance_base}, alpha_spent=alpha_cost_per_trial)
            results.append({"hypothesis_id": hypothesis.hypothesis_id, "evidence": str(path), "validation_sharpe": result.validation_score(), "test": result.metrics["test"].__dict__})
        best = max(results, key=lambda item: item["validation_sharpe"], default=None)
        if best is None or best["validation_sharpe"] <= 0:
            self.campaign.propose(kind="workflow", description="Improve RSI hypothesis generation after non-positive validation frontier")
        current = self.campaign.current
        return {
            "generation": current.number,
            "novelty": novelty_result,
            "trials": results,
            "selected_by_validation": best,
            "alpha_cost_per_trial": alpha_cost_per_trial,
            "alpha_spent": current.alpha_spent,
            "remaining_alpha_budget": current.remaining_budget,
            "provenance": provenance_base,
            "status": "complete",
        }
