"""Small CLI for starting and running offline RSI research campaigns."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .agent import RecursiveRSIAgent
from .campaign import RecursiveCampaign
from .contracts import SplitSpec


def _read_close(path: str, column: str) -> list[float]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = csv.DictReader(handle)
        try:
            return [float(row[column]) for row in rows]
        except KeyError as exc:
            raise SystemExit(f"missing close column: {column}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rsi-research")
    sub = parser.add_subparsers(dest="command", required=True)
    start = sub.add_parser("start")
    start.add_argument("--state", default="artifacts/campaign.json")
    start.add_argument("--dataset-hash", required=True)
    start.add_argument("--alpha-budget", type=float, default=0.01)
    status = sub.add_parser("status")
    status.add_argument("--state", default="artifacts/campaign.json")
    run = sub.add_parser("run")
    run.add_argument("--data", required=True)
    run.add_argument("--close-column", default="close")
    run.add_argument("--state", default="artifacts/campaign.json")
    run.add_argument("--evidence-dir", default="artifacts/evidence")
    run.add_argument("--train-end", type=int, required=True)
    run.add_argument("--validation-end", type=int, required=True)
    run.add_argument("--test-end", type=int)
    args = parser.parse_args(argv)
    campaign = RecursiveCampaign(args.state)
    if args.command == "start":
        print(json.dumps(campaign.start(knowledge_snapshot=[], dataset_hash=args.dataset_hash, skill_version="rsi-agent@1", alpha_budget=args.alpha_budget).__dict__, indent=2))
        return 0
    if args.command == "status":
        print(json.dumps(campaign.summary(), indent=2, ensure_ascii=False))
        return 0
    close = _read_close(args.data, args.close_column)
    result = RecursiveRSIAgent(campaign, evidence_dir=args.evidence_dir).run_generation(close, SplitSpec(args.train_end, args.validation_end, args.test_end))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
