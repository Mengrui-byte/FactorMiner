"""Stable contracts shared by the RSI agent, evaluator, and integrations."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


def canonical_hash(value: Any) -> str:
    """Hash a JSON-compatible value using the repository evidence convention."""

    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class SplitSpec:
    """Timestamp-index split boundaries expressed as integer offsets.

    ``train_end`` and ``validation_end`` are exclusive.  The test split runs
    from ``validation_end`` to ``test_end`` (or the end of the input).
    """

    train_end: int
    validation_end: int
    test_end: int | None = None

    def validate(self, length: int) -> None:
        if length < 3:
            raise ValueError("at least three observations are required")
        end = self.test_end if self.test_end is not None else length
        if self.train_end < 1 or self.validation_end <= self.train_end:
            raise ValueError("split boundaries must satisfy 0 < train_end < validation_end")
        if end <= self.validation_end or end > length:
            raise ValueError("test_end must satisfy validation_end < test_end <= data length")

    def slices(self, length: int) -> dict[str, slice]:
        self.validate(length)
        end = self.test_end if self.test_end is not None else length
        return {
            "train": slice(0, self.train_end),
            "validation": slice(self.train_end, self.validation_end),
            "test": slice(self.validation_end, end),
        }

    def entry_bounds(self, length: int, horizon: int) -> dict[str, tuple[int, int]]:
        """Return entry ranges whose complete forward label remains in one split."""

        self.validate(length)
        if horizon < 1 or horizon >= length:
            raise ValueError("horizon must satisfy 1 <= horizon < data length")
        end = self.test_end if self.test_end is not None else length
        bounds = {
            "train": (0, max(0, self.train_end - horizon)),
            "validation": (
                self.train_end,
                max(self.train_end, self.validation_end - horizon),
            ),
            "test": (
                self.validation_end,
                max(self.validation_end, end - horizon),
            ),
        }
        for name, (start, stop) in bounds.items():
            if stop <= start:
                raise ValueError(f"{name} split is too short for horizon={horizon}")
        return bounds


@dataclass(frozen=True)
class Hypothesis:
    """A pre-declared RSI experiment family member."""

    hypothesis_id: str
    window: int = 14
    lower: float = 30.0
    upper: float = 70.0
    horizon: int = 1
    regime: str = "all"
    rationale: str = "Canonical Wilder RSI mean-reversion baseline"
    null_model: str = "buy_and_hold"

    def validate(self) -> None:
        if self.window < 2:
            raise ValueError("RSI window must be >= 2")
        if not 0.0 < self.lower < self.upper < 100.0:
            raise ValueError("RSI thresholds must satisfy 0 < lower < upper < 100")
        if self.horizon < 1:
            raise ValueError("horizon must be >= 1")
        if self.regime != "all":
            raise ValueError("only the declared 'all' regime is implemented")


@dataclass(frozen=True)
class ExperimentProvenance:
    """Inputs that determine how a result was generated and selected."""

    generation: int = 0
    knowledge_snapshot_hash: str = ""
    novelty_hash: str = ""
    skill_version: str = "rsi-agent@1"
    planner_version: str = "rule-based@1"
    operator_registry_hash: str = "rsi-wilder@1"
    trial_family_hash: str = ""
    selection_rule: str = "validation_sharpe_max_only"
    alpha_cost_per_trial: float = 0.0


@dataclass
class SplitMetrics:
    """Metrics for one fixed timestamp split."""

    sharpe: float
    total_return: float
    max_drawdown: float
    turnover: float
    observations: int


@dataclass
class ExperimentResult:
    """Reproducible output from one hypothesis over all splits."""

    hypothesis: Hypothesis
    dataset_hash: str
    split: SplitSpec
    cost_bps: float
    metrics: dict[str, SplitMetrics]
    rsi_warmup: int
    trial_index: int
    provenance: ExperimentProvenance = field(default_factory=ExperimentProvenance)
    warnings: list[str] = field(default_factory=list)
    evidence_id: str | None = None

    def validation_score(self) -> float:
        return self.metrics["validation"].sharpe

    def as_dict(self) -> dict[str, Any]:
        return {
            "hypothesis": self.hypothesis.__dict__,
            "dataset_hash": self.dataset_hash,
            "split": self.split.__dict__,
            "cost_bps": self.cost_bps,
            "metrics": {key: value.__dict__ for key, value in self.metrics.items()},
            "rsi_warmup": self.rsi_warmup,
            "trial_index": self.trial_index,
            "provenance": self.provenance.__dict__,
            "warnings": self.warnings,
            "evidence_id": self.evidence_id,
        }
