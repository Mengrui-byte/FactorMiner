"""Causal RSI calculation and offline evaluation."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence

import numpy as np

from .contracts import ExperimentResult, Hypothesis, SplitMetrics, SplitSpec


def dataset_fingerprint(close: Sequence[float], timestamps: Sequence[str] | None = None) -> str:
    """Return a stable fingerprint for the exact input series and timestamps."""

    values = np.asarray(close, dtype=np.float64)
    payload = {
        "close_sha256": hashlib.sha256(values.tobytes()).hexdigest(),
        "length": int(values.size),
        "timestamps": list(timestamps) if timestamps is not None else None,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _wilder_average(values: np.ndarray, window: int) -> np.ndarray:
    out = np.full(values.shape, np.nan, dtype=np.float64)
    state = np.nan
    seed: list[float] = []
    alpha = 1.0 / window
    for index, value in enumerate(values):
        if not np.isfinite(value):
            state = np.nan
            seed.clear()
            continue
        if np.isnan(state):
            seed.append(float(value))
            if len(seed) == window:
                state = float(np.mean(seed))
                out[index] = state
        else:
            state = (1.0 - alpha) * state + alpha * float(value)
            out[index] = state
    return out


def wilder_rsi(close: Sequence[float], window: int = 14) -> np.ndarray:
    """Compute Wilder RSI causally; missing observations reset the warm-up."""

    if window < 2:
        raise ValueError("window must be >= 2")
    prices = np.asarray(close, dtype=np.float64)
    if prices.ndim != 1:
        raise ValueError("close must be a one-dimensional series")
    delta = np.full(prices.shape, np.nan, dtype=np.float64)
    delta[1:] = np.diff(prices)
    finite = np.isfinite(prices) & np.isfinite(np.concatenate(([np.nan], prices[:-1])))
    gains = np.where(finite, np.maximum(delta, 0.0), np.nan)
    losses = np.where(finite, np.maximum(-delta, 0.0), np.nan)
    average_gain = _wilder_average(gains, window)
    average_loss = _wilder_average(losses, window)
    result = np.full(prices.shape, np.nan, dtype=np.float64)
    valid = np.isfinite(average_gain) & np.isfinite(average_loss)
    with np.errstate(divide="ignore", invalid="ignore"):
        relative_strength = np.divide(
            average_gain,
            average_loss,
            out=np.full(prices.shape, np.inf),
            where=average_loss > 0,
        )
        result[valid] = 100.0 - 100.0 / (1.0 + relative_strength[valid])
    result[valid & (average_gain == 0) & (average_loss == 0)] = 50.0
    return result


def _metrics(returns: np.ndarray, positions: np.ndarray) -> SplitMetrics:
    finite = np.isfinite(returns)
    values = returns[finite]
    if values.size == 0:
        return SplitMetrics(0.0, 0.0, 0.0, 0.0, 0)
    equity = np.cumprod(1.0 + values)
    peak = np.maximum.accumulate(equity)
    drawdown = equity / peak - 1.0
    volatility = float(np.std(values, ddof=1)) if values.size > 1 else 0.0
    sharpe = float(np.mean(values) / volatility * np.sqrt(252.0)) if volatility > 0 else 0.0
    turnover = float(np.mean(np.abs(np.diff(np.r_[0.0, positions[: values.size]]))))
    return SplitMetrics(
        sharpe=sharpe,
        total_return=float(equity[-1] - 1.0),
        max_drawdown=float(np.min(drawdown)),
        turnover=turnover,
        observations=int(values.size),
    )


def evaluate_hypothesis(
    close: Sequence[float],
    hypothesis: Hypothesis,
    split: SplitSpec,
    *,
    cost_bps: float = 5.0,
    dataset_hash: str | None = None,
    trial_index: int = 0,
) -> ExperimentResult:
    """Evaluate one hypothesis with signal-at-t applied to return t->t+1."""

    hypothesis.validate()
    prices = np.asarray(close, dtype=np.float64)
    boundaries = split.slices(len(prices))
    rsi = wilder_rsi(prices, hypothesis.window)
    signal = np.where(rsi < hypothesis.lower, 1.0, np.where(rsi > hypothesis.upper, -1.0, 0.0))
    forward_returns = np.full(len(prices), np.nan, dtype=np.float64)
    forward_returns[:-hypothesis.horizon] = (
        prices[hypothesis.horizon :] / prices[:-hypothesis.horizon] - 1.0
    )
    positions = signal.copy()
    position_change = np.abs(np.diff(np.r_[0.0, positions]))
    strategy_returns = positions * forward_returns - position_change * (cost_bps / 10000.0)
    metrics = {
        name: _metrics(strategy_returns[index_slice], positions[index_slice])
        for name, index_slice in boundaries.items()
    }
    warnings = []
    if not np.isfinite(prices).all():
        warnings.append("missing close observations reset RSI warm-up and are excluded")
    return ExperimentResult(
        hypothesis=hypothesis,
        dataset_hash=dataset_hash or dataset_fingerprint(prices),
        split=split,
        cost_bps=float(cost_bps),
        metrics=metrics,
        rsi_warmup=hypothesis.window,
        trial_index=trial_index,
        warnings=warnings,
    )
