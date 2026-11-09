#!/usr/bin/env python3
"""Verify historical implementation bytes without consulting mutable worktree paths."""

import argparse
import json
from pathlib import Path

from tileplace_provenance import content_sha256
from tileplace_vpr import ContractError, sha256


def verify_archive(implementation, root):
    identity = {"parser": implementation["parser"], "sources": [
        {"name": r["name"], "sha256": r["sha256"]} for r in implementation["sources"]]}
    if content_sha256(identity) != implementation["sha256"]:
        raise ContractError("implementation identity does not match source records")
    directory = root / implementation["sha256"]
    archive = json.loads((directory / "archive.json").read_text())
    expected = [(r["name"], r["sha256"]) for r in implementation["sources"]]
    if archive.get("schema") == "TILEPLACE_IMPLEMENTATION_SOURCE_ARCHIVE_V1":
        archived_identity = archive.get("implementation_sha256")
    elif archive.get("schema") == "TILEPLACE_IMPLEMENTATION_V1" and archive.get("parser") == implementation["parser"]:
        archived_identity = archive.get("sha256")
    else:
        raise ContractError("unsupported or mismatched archive metadata")
    if (archived_identity != implementation["sha256"]
            or [(r["name"], r["sha256"]) for r in archive["sources"]] != expected
            or len({name for name, _ in expected}) != len(expected)):
        raise ContractError("archive metadata differs")
    for name, digest in expected:
        if Path(name).name != name or name in {".", ".."}:
            raise ContractError("invalid archived source name")
        if sha256(directory / name) != digest:
            raise ContractError(f"archived source bytes differ: {name}")
    return {"implementation_sha256": implementation["sha256"],
            "verified_source_files": len(expected), "status": "pass"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / "experiments" / "implementation_sources"
    print(json.dumps(verify_archive(json.loads(args.manifest.read_text()), root), sort_keys=True))


if __name__ == "__main__":
    main()
