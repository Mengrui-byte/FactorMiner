"""Recursive RSI research agent with a deterministic and Harness-pluggable planner."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import Any, Protocol

from .backtest import dataset_fingerprint, evaluate_hypothesis
from .campaign import RecursiveCampaign
from .contracts import Hypothesis, SplitSpec
from .evidence import write_evidence
from .knowledge import KnowledgeProvider, LocalKnowledge


class Planner(Protocol):
    def propose(self, context: dict[str, Any]) -> list[Hypothesis]: ...


@dataclass
class RuleBasedPlanner:
    """Offline fallback planner; DeepSeek Harness can replace it through a command."""

    max_trials: int = 6

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
        return [Hypothesis(**item) for item in payload["hypotheses"]]


@dataclass
class RecursiveRSIAgent:
    campaign: RecursiveCampaign
    knowledge: KnowledgeProvider | None = None
    planner: Planner | None = None
    evidence_dir: str = "artifacts/evidence"

    def run_generation(self, close: list[float], split: SplitSpec, *, cost_bps: float = 5.0, skill_version: str = "rsi-agent@1", knowledge_snapshot: list[dict[str, Any]] | None = None, novelty: dict[str, Any] | None = None) -> dict[str, Any]:
        provider = self.knowledge or LocalKnowledge(knowledge_snapshot or [])
        planner = self.planner or DeepSeekHarnessPlanner()
        data_hash = dataset_fingerprint(close)
        if self.campaign.current is None:
            snapshot = provider.search("RSI time-series momentum reversal regimes", limit=5)
            self.campaign.start(knowledge_snapshot=snapshot, dataset_hash=data_hash, skill_version=skill_version)
        context = {"generation": self.campaign.current.number, "knowledge": provider.search("RSI momentum reversal", limit=5), "dataset_hash": data_hash, "split": split.__dict__, "cost_bps": cost_bps}
        novelty_result = novelty or provider.novelty("RSI threshold-conditioned reversal")
        context["novelty"] = novelty_result
        hypotheses = planner.propose(context)
        results = []
        for index, hypothesis in enumerate(hypotheses, start=1):
            result = evaluate_hypothesis(close, hypothesis, split, cost_bps=cost_bps, dataset_hash=data_hash, trial_index=index)
            path = write_evidence(result, self.evidence_dir)
            self.campaign.record_result({"evidence_id": result.evidence_id, "hypothesis_id": hypothesis.hypothesis_id, "validation_sharpe": result.validation_score()}, alpha_spent=0.0)
            results.append({"hypothesis_id": hypothesis.hypothesis_id, "evidence": str(path), "validation_sharpe": result.validation_score(), "test": result.metrics["test"].__dict__})
        best = max(results, key=lambda item: item["validation_sharpe"], default=None)
        if best is None or best["validation_sharpe"] <= 0:
            self.campaign.propose(kind="workflow", description="Improve RSI hypothesis generation after non-positive validation frontier")
        return {"generation": self.campaign.current.number, "novelty": novelty_result, "trials": results, "selected_by_validation": best, "status": "complete"}
