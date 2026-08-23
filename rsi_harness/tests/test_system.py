from __future__ import annotations

import json

import numpy as np

from rsi_harness.agent import RecursiveRSIAgent, RuleBasedPlanner
from rsi_harness.backtest import evaluate_hypothesis, wilder_rsi
from rsi_harness.campaign import RecursiveCampaign
from rsi_harness.contracts import Hypothesis, SplitSpec
from rsi_harness.evidence import verify_evidence


def test_rsi_boundaries_and_missing_reset() -> None:
    close = np.array([1, 2, 3, 4, 5, np.nan, 6, 7, 8], dtype=float)
    rsi = wilder_rsi(close, 3)
    assert np.all(rsi[3:5] == 100.0)
    assert np.isnan(rsi[5:]).all()


def test_evaluation_applies_signal_to_next_return() -> None:
    close = np.linspace(100, 110, 30)
    result = evaluate_hypothesis(close, Hypothesis("up", 3, 30, 70), SplitSpec(10, 20))
    assert result.metrics["train"].observations == 10
    # The final test timestamp has no t->t+1 return and is excluded.
    assert result.metrics["test"].observations == 9


def test_campaign_gate_and_agent_round_trip(tmp_path) -> None:
    campaign = RecursiveCampaign(tmp_path / "campaign.json")
    agent = RecursiveRSIAgent(campaign, planner=RuleBasedPlanner(max_trials=2), evidence_dir=tmp_path / "evidence")
    close = (100 + np.sin(np.arange(80) / 3.0) * 5 + np.arange(80) * 0.05).tolist()
    output = agent.run_generation(
        close,
        SplitSpec(35, 55),
        skill_version="test@1",
        knowledge_snapshot=[{"id": "rsi-note", "text": "RSI reversal"}],
        novelty={"status": "PARTIALLY-KNOWN"},
    )
    assert output["status"] == "complete"
    assert output["novelty"]["status"] == "PARTIALLY-KNOWN"
    assert len(output["trials"]) == 2
    assert campaign.current is not None
    evidence = list((tmp_path / "evidence").glob("*.json"))
    assert len(evidence) == 2
    assert verify_evidence(evidence[0]) == evidence[0].stem
    proposal = campaign.propose(kind="operator", description="duration in extreme zone")
    assert campaign.benchmark(proposal.proposal_id, parent_score=0.1, candidate_score=0.2, checks={"unit": True}).status == "validated"
    payload = json.loads((tmp_path / "campaign.json").read_text())
    assert payload["schema_version"] == 2
