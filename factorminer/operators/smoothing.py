"""Moving average / smoothing operators.

Input shape: ``(M, T)`` -> output shape ``(M, T)``.
All operate along the time axis (axis=1) per asset row.
"""

from __future__ import annotations

import numpy as np

try:
    import torch
except ImportError:
    torch = None  # type: ignore[assignment]


# ===========================================================================
# NumPy implementations
# ===========================================================================

def sma_np(x: np.ndarray, window: int = 10) -> np.ndarray:
    """Simple moving average (identical to Mean)."""
    window = int(window)
    M, T = x.shape
    out = np.full_like(x, np.nan, dtype=np.float64)
    # Cumsum trick for O(1) per element
    cs = np.nancumsum(x, axis=1)
    out[:, window - 1:] = cs[:, window - 1:]
    if window > 1:
        out[:, window - 1:] -= np.concatenate(
            [np.zeros((M, 1), dtype=np.float64), cs[:, :-window]], axis=1
        )[:, :T - window + 1]  # fix: just subtract shifted cumsum
        out[:, window - 1:] = (cs[:, window - 1:] - np.concatenate(
            [np.zeros((M, 1), dtype=np.float64), cs[:, :-1]], axis=1
        )[:, :T - window + 1])
    out[:, window - 1:] /= window
    out[:, :window - 1] = np.nan
    return out


def ema_np(x: np.ndarray, window: int = 10) -> np.ndarray:
    """Exponential moving average with span = window."""
    window = int(window)
    alpha = 2.0 / (window + 1.0)
    M, T = x.shape
    out = np.copy(x).astype(np.float64)
    for t in range(1, T):
        prev = out[:, t - 1]
        curr = x[:, t]
        prev_valid = ~np.isnan(prev)
        curr_valid = ~np.isnan(curr)
        both_valid = prev_valid & curr_valid
        only_prev = prev_valid & ~curr_valid
        # Full-column where avoids boolean advanced-index allocations each step.
        out[:, t] = np.where(
            both_valid,
            alpha * curr + (1.0 - alpha) * prev,
            np.where(only_prev, prev, out[:, t]),
        )
    return out


def dema_np(x: np.ndarray, window: int = 10) -> np.ndarray:
    """Double EMA: 2 * EMA(x) - EMA(EMA(x))."""
    e1 = ema_np(x, window)
    e2 = ema_np(e1, window)
    return 2.0 * e1 - e2


def kama_np(x: np.ndarray, window: int = 10) -> np.ndarray:
    """Kaufman Adaptive Moving Average.

    Efficiency: rolling absolute-change sums are precomputed with a prefix
    sum so each time step is O(1) instead of O(window).  The sequential
    adaptive update remains O(T) because it depends on the prior KAMA value.
    """
    window = int(window)
    fast_sc = 2.0 / (2.0 + 1.0)
    slow_sc = 2.0 / (30.0 + 1.0)
    M, T = x.shape
    out = np.copy(x).astype(np.float64)
    if T <= window:
        return out

    # abs step changes; nansum(window) ≡ sum of nan_to_num over the same span
    step_abs = np.zeros((M, T), dtype=np.float64)
    step_abs[:, 1:] = np.abs(np.diff(x, axis=1))
    step_abs = np.nan_to_num(step_abs, nan=0.0)
    # padded prefix: pref[:, t+1] = sum(step_abs[:, :t+1])
    pref = np.empty((M, T + 1), dtype=np.float64)
    pref[:, 0] = 0.0
    np.cumsum(step_abs, axis=1, out=pref[:, 1:])

    for t in range(window, T):
        direction = np.abs(x[:, t] - x[:, t - window])
        # sum of abs diffs over x[t-window:t+1] consecutive pairs
        volatility = pref[:, t + 1] - pref[:, t - window + 1]
        er = np.divide(
            direction,
            volatility,
            out=np.zeros_like(direction, dtype=np.float64),
            where=volatility > 1e-10,
        )
        sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
        prev = out[:, t - 1]
        curr = x[:, t]
        valid = ~np.isnan(prev) & ~np.isnan(curr)
        out[:, t] = np.where(valid, prev + sc * (curr - prev), out[:, t])
    return out


def hma_np(x: np.ndarray, window: int = 10) -> np.ndarray:
    """Hull Moving Average: WMA(2*WMA(x, w/2) - WMA(x, w), sqrt(w))."""
    window = int(window)
    from factorminer.operators.timeseries import wma_np
    half = max(int(window / 2), 1)
    sqrt_w = max(int(np.sqrt(window)), 1)
    w1 = wma_np(x, half)
    w2 = wma_np(x, window)
    diff = 2.0 * w1 - w2
    return wma_np(diff, sqrt_w)


def rma_np(x: np.ndarray, window: int = 14) -> np.ndarray:
    """Wilder's moving average, seeded by the first complete window.

    The recursive update is causal and preserves a leading warm-up region. NaN
    observations do not advance the state; a row becomes valid again only once
    a complete finite seed window is available.
    """
    window = int(window)
    if window < 2:
        raise ValueError("RMA window must be >= 2")
    M, T = x.shape
    out = np.full((M, T), np.nan, dtype=np.float64)
    alpha = 1.0 / window
    for row in range(M):
        state = np.nan
        valid_run = 0
        seed_sum = 0.0
        for t in range(T):
            value = x[row, t]
            if not np.isfinite(value):
                state = np.nan
                valid_run = 0
                seed_sum = 0.0
                continue
            if np.isnan(state):
                valid_run += 1
                seed_sum += value
                if valid_run == window:
                    state = seed_sum / window
                    out[row, t] = state
            else:
                state = (1.0 - alpha) * state + alpha * value
                out[row, t] = state
    return out


def rsi_np(x: np.ndarray, window: int = 14) -> np.ndarray:
    """Wilder RSI computed from close prices without future information."""
    window = int(window)
    if window < 2:
        raise ValueError("RSI window must be >= 2")
    M, T = x.shape
    out = np.full((M, T), np.nan, dtype=np.float64)
    if T <= window:
        return out
    for row in range(M):
        prices = x[row]
        gains = np.full(T, np.nan, dtype=np.float64)
        losses = np.full(T, np.nan, dtype=np.float64)
        delta = np.diff(prices)
        finite = np.isfinite(prices[1:]) & np.isfinite(prices[:-1])
        gains[1:][finite] = np.maximum(delta[finite], 0.0)
        losses[1:][finite] = np.maximum(-delta[finite], 0.0)
        avg_gain = rma_np(gains[None, :], window)[0]
        avg_loss = rma_np(losses[None, :], window)[0]
        valid = np.isfinite(avg_gain) & np.isfinite(avg_loss)
        with np.errstate(divide="ignore", invalid="ignore"):
            rs = np.divide(avg_gain, avg_loss, out=np.full(T, np.inf), where=avg_loss > 0)
            values = 100.0 - (100.0 / (1.0 + rs))
        both_zero = valid & (avg_gain == 0) & (avg_loss == 0)
        values[both_zero] = 50.0
        out[row, valid] = values[valid]
    return out


# ===========================================================================
# PyTorch implementations
# ===========================================================================

def sma_torch(x: torch.Tensor, window: int = 10) -> torch.Tensor:
    """Simple moving average using conv1d for GPU efficiency."""
    window = int(window)
    M, T = x.shape
    # Use unfold-based approach
    from factorminer.operators.statistical import _pad_front_torch, _unfold_torch
    w = _unfold_torch(x, window)
    result = w.nanmean(dim=2)
    return _pad_front_torch(result, window, T)


def ema_torch(x: torch.Tensor, window: int = 10) -> torch.Tensor:
    """EMA -- sequential by nature, but batch across assets."""
    window = int(window)
    alpha = 2.0 / (window + 1.0)
    M, T = x.shape
    out = x.clone()
    for t in range(1, T):
        prev = out[:, t - 1]
        curr = x[:, t]
        prev_valid = ~torch.isnan(prev)
        curr_valid = ~torch.isnan(curr)
        both_valid = prev_valid & curr_valid
        only_prev = prev_valid & ~curr_valid
        out[:, t] = torch.where(
            both_valid,
            alpha * curr + (1.0 - alpha) * prev,
            torch.where(only_prev, prev, out[:, t]),
        )
    return out


def dema_torch(x: torch.Tensor, window: int = 10) -> torch.Tensor:
    e1 = ema_torch(x, window)
    e2 = ema_torch(e1, window)
    return 2.0 * e1 - e2


def kama_torch(x: torch.Tensor, window: int = 10) -> torch.Tensor:
    window = int(window)
    fast_sc = 2.0 / (2.0 + 1.0)
    slow_sc = 2.0 / (30.0 + 1.0)
    M, T = x.shape
    out = x.clone()
    if T <= window:
        return out

    step_abs = torch.zeros_like(x)
    step_abs[:, 1:] = x.diff(dim=1).abs()
    step_abs = torch.nan_to_num(step_abs, nan=0.0)
    pref = torch.zeros(M, T + 1, dtype=x.dtype, device=x.device)
    pref[:, 1:] = step_abs.cumsum(dim=1)

    for t in range(window, T):
        direction = (x[:, t] - x[:, t - window]).abs()
        vol = pref[:, t + 1] - pref[:, t - window + 1]
        er = torch.where(vol > 1e-10, direction / vol, torch.zeros_like(direction))
        sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
        prev = out[:, t - 1]
        curr = x[:, t]
        valid = ~torch.isnan(prev) & ~torch.isnan(curr)
        out[:, t] = torch.where(valid, prev + sc * (curr - prev), out[:, t])
    return out


def hma_torch(x: torch.Tensor, window: int = 10) -> torch.Tensor:
    window = int(window)
    from factorminer.operators.timeseries import wma_torch
    half = max(int(window / 2), 1)
    sqrt_w = max(int(window ** 0.5), 1)
    w1 = wma_torch(x, half)
    w2 = wma_torch(x, window)
    diff = 2.0 * w1 - w2
    return wma_torch(diff, sqrt_w)


# ===========================================================================
# Registration table
# ===========================================================================

SMOOTHING_OPS = {
    "EMA": (ema_np, ema_torch),
    "DEMA": (dema_np, dema_torch),
    "SMA": (sma_np, sma_torch),
    "KAMA": (kama_np, kama_torch),
    "HMA": (hma_np, hma_torch),
    "RMA": (rma_np, None),
    "RSI": (rsi_np, None),
}
