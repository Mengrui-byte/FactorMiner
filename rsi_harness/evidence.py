"""Content-addressed evidence packs for research results."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .contracts import ExperimentResult


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def write_evidence(result: ExperimentResult, directory: str | Path) -> Path:
    """Write an immutable JSON evidence pack and return its path."""

    payload = result.as_dict()
    payload.pop("evidence_id", None)
    payload["evidence_id"] = hashlib.sha256(_canonical(payload)).hexdigest()
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
    if not evidence_id or hashlib.sha256(_canonical(payload)).hexdigest() != evidence_id:
        raise ValueError(f"invalid evidence pack: {path}")
    return evidence_id


def result_to_json(result: ExperimentResult) -> dict[str, Any]:
    return asdict(result)
