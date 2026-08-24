"""MCP surface for the RSI recursive research controller."""

from __future__ import annotations

from typing import Any

from .agent import RecursiveRSIAgent
from .campaign import RecursiveCampaign
from .contracts import SplitSpec


def create_server(state_path: str = "artifacts/campaign.json", evidence_dir: str = "artifacts/evidence") -> Any:
    try:
        from mcp.server.fastmcp import FastMCP
    except ModuleNotFoundError as exc:  # pragma: no cover - optional runtime
        raise RuntimeError("install the MCP extra before starting rsi-mcp-serve") from exc

    server = FastMCP("rsi-recursive-research")

    @server.tool()
    def campaign_status() -> dict[str, Any]:
        return RecursiveCampaign(state_path).summary()

    @server.tool()
    def campaign_start(dataset_hash: str, alpha_budget: float = 0.01) -> dict[str, Any]:
        campaign = RecursiveCampaign(state_path)
        generation = campaign.start(knowledge_snapshot=[], dataset_hash=dataset_hash, skill_version="rsi-agent@1", alpha_budget=alpha_budget)
        return generation.__dict__

    @server.tool()
    def run_rsi(close: list[float], train_end: int, validation_end: int, test_end: int | None = None, cost_bps: float = 5.0, knowledge_snapshot: list[dict[str, Any]] | None = None, novelty: dict[str, Any] | None = None, skill_version: str = "rsi-agent@1", alpha_cost_per_trial: float = 0.001) -> dict[str, Any]:
        campaign = RecursiveCampaign(state_path)
        return RecursiveRSIAgent(campaign, evidence_dir=evidence_dir).run_generation(close, SplitSpec(train_end, validation_end, test_end), cost_bps=cost_bps, knowledge_snapshot=knowledge_snapshot, novelty=novelty, skill_version=skill_version, alpha_cost_per_trial=alpha_cost_per_trial)

    @server.tool()
    def capability_propose(kind: str, description: str, evidence_ids: list[str] | None = None) -> dict[str, Any]:
        return RecursiveCampaign(state_path).propose(kind=kind, description=description, evidence_ids=evidence_ids).__dict__

    @server.tool()
    def capability_benchmark(proposal_id: str, parent_score: float, candidate_score: float, checks: dict[str, bool]) -> dict[str, Any]:
        return RecursiveCampaign(state_path).benchmark(proposal_id, parent_score=parent_score, candidate_score=candidate_score, checks=checks).__dict__

    return server


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(prog="rsi-mcp-serve")
    parser.add_argument("--state", default="artifacts/campaign.json")
    parser.add_argument("--evidence-dir", default="artifacts/evidence")
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    args = parser.parse_args()
    create_server(args.state, args.evidence_dir).run(transport=args.transport)
