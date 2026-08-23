"""RSI recursive research system.

The package owns the complete project boundary: knowledge snapshots, causal
evaluation, evidence, budgets, and recursive agent state.
"""

from .backtest import evaluate_hypothesis, wilder_rsi
from .campaign import RecursiveCampaign
from .contracts import ExperimentResult, Hypothesis, SplitSpec

__all__ = [
    "ExperimentResult",
    "Hypothesis",
    "RecursiveCampaign",
    "SplitSpec",
    "evaluate_hypothesis",
    "wilder_rsi",
]
