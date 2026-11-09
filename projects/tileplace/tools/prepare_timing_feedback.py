#!/usr/bin/env python3
"""Extract ranked clustered-block path edges from a routed VPR timing report."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

from tileplace_vpr import ContractError, packed_atom_clusters, sha256


PATH = re.compile(r"^#Path\s+(\d+)\s*$")
# VPR prints architecture-specific primitive port names (for example
# ``in/out/Q/D/clk`` on VTR architectures and ``inpad/outpad/q`` on Titan).
# The atom lookup below remains the authority, so accepting any indexed port
# here does not admit report labels which are absent from the packed netlist.
POINT = re.compile(r"^\s*(\S+)\.[^\s.\[]+\[\d+\]")
GENERIC_POINT_PATTERN = POINT.pattern
PARSER_VERSION = "generic-indexed-port-v1"
Q16_MAX = 65535


def parser_identity() -> dict:
    return {
        "mode": PARSER_VERSION if POINT.pattern == GENERIC_POINT_PATTERN else "unregistered-regex",
        "point_pattern": POINT.pattern,
        "point_flags": POINT.flags,
        "path_pattern": PATH.pattern,
        "path_flags": PATH.flags,
    }


def parse_ranked_edges(
    report: Path,
    atom_to_block: dict[str, int],
    max_paths: int = 20,
) -> tuple[Counter[tuple[int, int]], set[int], int]:
    if max_paths <= 0:
        raise ContractError("timing-feedback path count must be positive")
    edges: Counter[tuple[int, int]] = Counter()
    focus: set[int] = set()
    current_rank: int | None = None
    current_blocks: list[int] = []
    parsed_paths = 0

    def flush() -> None:
        nonlocal parsed_paths
        if current_rank is None or current_rank > max_paths:
            return
        collapsed: list[int] = []
        for block_id in current_blocks:
            if not collapsed or collapsed[-1] != block_id:
                collapsed.append(block_id)
        if len(collapsed) < 2:
            return
        parsed_paths += 1
        focus.update(collapsed)
        rank_q16 = ((max_paths - current_rank + 1) * Q16_MAX) // max_paths
        path_edges = {
            tuple(sorted((source, sink)))
            for source, sink in zip(collapsed, collapsed[1:])
            if source != sink
        }
        for edge in path_edges:
            edges[edge] += rank_q16

    for line in report.read_text(encoding="utf-8", errors="replace").splitlines():
        match = PATH.match(line)
        if match:
            flush()
            current_rank = int(match.group(1))
            current_blocks = []
            if current_rank > max_paths:
                break
            continue
        if current_rank is None:
            continue
        point = POINT.match(line)
        if point and point.group(1) in atom_to_block:
            current_blocks.append(atom_to_block[point.group(1)])
    else:
        flush()
    if not edges or not focus or parsed_paths == 0:
        raise ContractError("timing report produced no mapped inter-cluster path edges")
    return edges, focus, parsed_paths


def prepare(report: Path, netlist: Path, blocks_jsonl: Path, max_paths: int = 20) -> dict:
    atom_clusters = packed_atom_clusters(netlist)
    block_ids = {
        str(row["name"]): int(row["block_id"])
        for row in (json.loads(line) for line in blocks_jsonl.read_text().splitlines())
    }
    atom_to_block = {
        atom: block_ids[cluster]
        for atom, cluster in atom_clusters.items()
        if cluster in block_ids
    }
    edges, focus, parsed_paths = parse_ranked_edges(report, atom_to_block, max_paths)
    return {
        "schema": "TILEPLACE_TIMING_FEEDBACK_V1",
        "status": "pass",
        "parser": parser_identity(),
        "max_paths": max_paths,
        "parsed_paths": parsed_paths,
        "focus_blocks": sorted(focus),
        "edges": [
            {"source_block_id": edge[0], "sink_block_id": edge[1], "weight_q16": weight}
            for edge, weight in sorted(edges.items())
        ],
        "inputs": {
            "timing_report": {"path": str(report.resolve()), "sha256": sha256(report)},
            "packed_netlist": {"path": str(netlist.resolve()), "sha256": sha256(netlist)},
            "blocks_jsonl": {"path": str(blocks_jsonl.resolve()), "sha256": sha256(blocks_jsonl)},
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timing-report", type=Path, required=True)
    parser.add_argument("--netlist", type=Path, required=True)
    parser.add_argument("--blocks-jsonl", type=Path, required=True)
    parser.add_argument("--max-paths", type=int, default=20)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = prepare(
            args.timing_report.resolve(), args.netlist.resolve(), args.blocks_jsonl.resolve(), args.max_paths
        )
        args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.output.resolve().write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({key: value for key, value in result.items() if key != "edges"}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"prepare_timing_feedback: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
