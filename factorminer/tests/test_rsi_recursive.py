from __future__ import annotations

import json

import numpy as np
import pytest

from factorminer.application.recursive_campaign import RecursiveCampaign
from factorminer.operators.registry import execute_operator, get_operator


def test_rma_uses_wilder_seed_and_causal_update() -> None:
    values = np.array([[1.0, 2.0, 3.0, 2.0, 2.0, 4.0]])
    result = execute_operator("RMA", values, params={"window": 3})
    expected = np.array([[np.nan, np.nan, 2.0, 2.0, 2.0, 2.6666666667]])
    np.testing.assert_allclose(result, expected, equal_nan=True, rtol=1e-10)


def test_rsi_monotone_and_flat_boundaries() -> None:
    up = np.arange(1.0, 20.0)[None, :]
    down = up[:, ::-1]
    flat = np.full((1, 20), 5.0)
    assert np.all(execute_operator("RSI", up, params={"window": 5})[0, 5:] == 100.0)
    assert np.all(execute_operator("RSI", down, params={"window": 5})[0, 5:] == 0.0)
    assert np.all(execute_operator("RSI", flat, params={"window": 5})[0, 5:] == 50.0)


def test_rsi_is_prefix_invariant_and_resets_after_missing_data() -> None:
    prices = np.array([[100, 101, 99, 100, 102, 101, 103, 104]], dtype=float)
    base = execute_operator("RSI", prices, params={"window": 3})
    extended = execute_operator(
        "RSI", np.concatenate([prices, [[105, 103]]], axis=1), params={"window": 3}
    )
    np.testing.assert_allclose(base, extended[:, : prices.shape[1]], equal_nan=True)

    prices[0, 5] = np.nan
    result = execute_operator("RSI", prices, params={"window": 3})
    assert np.isnan(result[0, 5:]).all()


def test_rsi_is_registered_with_guarded_window() -> None:
    spec = get_operator("RSI")
    assert spec.param_defaults["window"] == 14
    assert spec.param_ranges["window"] == (2.0, 250.0)


def test_recursive_campaign_requires_benchmarked_improvement(tmp_path) -> None:
    path = tmp_path / "campaign.json"
    campaign = RecursiveCampaign(path)
    first = campaign.start(
        knowledge_snapshot={"nodes": ["momentum/reversal"]},
        operator_registry=["RSI", "RMA"],
        skill_version="rsi-research@1",
        dataset_hash="data-v1",
    )
    assert first.generation == 0
    proposal = campaign.propose_capability(
        kind="operator",
        description="Add duration-in-extreme-zone operator",
        evidence_ids=["result-001"],
    )
    rejected = campaign.benchmark_capability(
        proposal.proposal_id,
        parent_score=0.5,
        candidate_score=0.5,
        checks={"unit_tests": True, "no_lookahead": True},
    )
    assert rejected.status == "rejected"
    proposal2 = campaign.propose_capability(kind="skill", description="Add regime review")
    accepted = campaign.benchmark_capability(
        proposal2.proposal_id,
        parent_score=0.5,
        candidate_score=0.7,
        checks={"unit_tests": True, "no_lookahead": True, "blind_benchmark": True},
    )
    assert accepted.status == "validated"
    second = campaign.next_generation(
        knowledge_snapshot={"nodes": ["momentum/reversal", "rsi-duration"]},
        operator_registry=["RSI", "RMA", "DurationBelow"],
        skill_version="rsi-research@2",
        dataset_hash="data-v1",
        trial_count=8,
        alpha_spent=0.001,
        anomalies=["extreme-zone-duration"],
    )
    assert second.parent_generation == 0
    saved = json.loads(path.read_text())
    assert saved["generations"][1]["alpha_budget_remaining"] == pytest.approx(0.009)
