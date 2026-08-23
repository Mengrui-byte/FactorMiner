"""RSI recursive research system.

The package is the project-level orchestration layer.  The existing
``factorminer`` package remains available as a compatible numerical engine,
while this package owns knowledge, evidence, budgets, and recursive agent
state.
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
