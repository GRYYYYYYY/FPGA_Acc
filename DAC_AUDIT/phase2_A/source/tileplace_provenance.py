"""Content identities for a TilePlace implementation and its feedback inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tileplace_vpr import ContractError, sha256


def content_sha256(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def source_snapshot(paths: list[Path], parser: dict) -> dict:
    records = [{"name": path.name, "path": str(path.resolve()), "sha256": sha256(path)}
               for path in sorted(set(paths))]
    identity = {"parser": parser, "sources": [{"name": r["name"], "sha256": r["sha256"]} for r in records]}
    return {"schema": "TILEPLACE_IMPLEMENTATION_V1", "sha256": content_sha256(identity),
            "parser": parser, "sources": records}


def file_snapshot(paths: list[Path]) -> list[dict]:
    return [{"path": str(path.resolve()), "sha256": sha256(path)} for path in sorted(set(paths))]


def verify_files(records: list[dict]) -> None:
    for record in records:
        if sha256(Path(record["path"])) != record["sha256"]:
            raise ContractError(f"source/input changed during search: {record['path']}")


def verify_implementation(actual: dict, expected: dict) -> None:
    if actual["sha256"] != expected.get("sha256") or actual["parser"] != expected.get("parser"):
        raise ContractError("implementation/parser differs from sealed implementation manifest")


def feedback_identity(payload: dict) -> str:
    # Paths and source-file annotations do not define the numerical feedback.
    return content_sha256({k: v for k, v in payload.items() if k not in {"inputs", "parser"}})
