"""Content-addressed evidence packs for research results."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .contracts import ExperimentResult, canonical_hash


def write_evidence(result: ExperimentResult, directory: str | Path) -> Path:
    """Write an immutable JSON evidence pack and return its path."""

    payload = result.as_dict()
    payload.pop("evidence_id", None)
    payload["evidence_id"] = canonical_hash(payload)
    result.evidence_id = payload["evidence_id"]
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"{payload['evidence_id']}.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != payload:
            raise ValueError(f"evidence hash collision or mutation: {path}")
        return path
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def verify_evidence(path: str | Path) -> str:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    evidence_id = payload.pop("evidence_id", None)
    if not evidence_id or canonical_hash(payload) != evidence_id:
        raise ValueError(f"invalid evidence pack: {path}")
    return evidence_id


def result_to_json(result: ExperimentResult) -> dict[str, Any]:
    return asdict(result)
