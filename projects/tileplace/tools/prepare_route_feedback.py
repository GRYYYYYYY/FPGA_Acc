#!/usr/bin/env python3
"""Convert a native VPR route and RR graph into TilePlace V2 edge pressure."""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

from tileplace_vpr import ContractError, sha256


NET = re.compile(r"^\s*Net\s+(\d+)\s+\(")
NODE = re.compile(r"^\s*Node:\s*(\d+)\s+(SOURCE|SINK|OPIN|IPIN|CHANX|CHANY)\b")
Q16 = 1 << 16


def route_occupancy(path: Path) -> Counter[int]:
    occupancy: Counter[int] = Counter()
    current_nodes: set[int] = set()

    def flush() -> None:
        occupancy.update(current_nodes)
        current_nodes.clear()

    active = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if NET.match(line):
            if active:
                flush()
            active = True
            continue
        match = NODE.match(line)
        if active and match and match.group(2) in {"CHANX", "CHANY"}:
            current_nodes.add(int(match.group(1)))
    if active:
        flush()
    if not occupancy:
        raise ContractError("route contains no CHANX/CHANY occupancy")
    return occupancy


def edge_pressure(rr_graph: Path, occupancy: Counter[int]) -> list[dict[str, int]]:
    needed = set(occupancy)
    edge_occupancy: Counter[tuple[int, int, int, int]] = Counter()
    edge_capacity: Counter[tuple[int, int, int, int]] = Counter()
    seen: set[int] = set()
    stack: list[ET.Element] = []
    for event, element in ET.iterparse(rr_graph, events=("start", "end")):
        if event == "start":
            stack.append(element)
            continue
        tag = element.tag.rsplit("}", 1)[-1]
        parent = stack[-2] if len(stack) >= 2 else None
        if tag == "rr_nodes":
            stack.pop()
            break
        if tag != "node":
            stack.pop()
            continue
        node_id = int(element.attrib["id"])
        kind = element.attrib.get("type")
        if kind not in {"CHANX", "CHANY"}:
            if parent is not None:
                parent.remove(element)
            element.clear()
            stack.pop()
            continue
        loc = element.find("loc")
        if loc is None:
            raise ContractError(f"RR channel node {node_id} is missing geometry")
        capacity = max(1, int(element.attrib.get("capacity", "1")))
        xlow, xhigh = int(loc.attrib["xlow"]), int(loc.attrib["xhigh"])
        ylow, yhigh = int(loc.attrib["ylow"]), int(loc.attrib["yhigh"])
        edges = []
        if kind == "CHANX":
            y = ylow
            edges = [(x, y, x + 1, y) for x in range(xlow, xhigh)]
        else:
            x = xlow
            edges = [(x, y, x, y + 1) for y in range(ylow, yhigh)]
        for key in edges:
            edge_capacity[key] += capacity
            if node_id in needed:
                edge_occupancy[key] += occupancy[node_id]
        if node_id in needed:
            seen.add(node_id)
        if parent is not None:
            parent.remove(element)
        element.clear()
        stack.pop()
    missing = sorted(needed - seen)
    if missing:
        raise ContractError(f"RR graph is missing {len(missing)} routed channel nodes")
    rows = []
    for key in sorted(edge_capacity):
        used = edge_occupancy[key]
        capacity = edge_capacity[key]
        pressure_q16 = (used * used * Q16 + capacity * capacity // 2) // (capacity * capacity)
        rows.append(
            {
                "x0": key[0],
                "y0": key[1],
                "x1": key[2],
                "y1": key[3],
                "occupancy": used,
                "capacity": capacity,
                "pressure_q16": pressure_q16,
            }
        )
    return rows


def prepare(route: Path, rr_graph: Path) -> dict:
    occupancy = route_occupancy(route)
    edges = edge_pressure(rr_graph, occupancy)
    return {
        "schema": "TILEPLACE_ROUTE_FEEDBACK_V1",
        "status": "pass",
        "inputs": {
            "route": {"path": str(route.resolve()), "sha256": sha256(route)},
            "rr_graph": {"path": str(rr_graph.resolve()), "sha256": sha256(rr_graph)},
        },
        "routed_channel_nodes": len(occupancy),
        "channel_node_uses": sum(occupancy.values()),
        "edge_count": len(edges),
        "edges": edges,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route", type=Path, required=True)
    parser.add_argument("--rr-graph", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = prepare(args.route.resolve(), args.rr_graph.resolve())
        args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.output.resolve().write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps({key: value for key, value in report.items() if key != "edges"}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, ET.ParseError) as error:
        print(f"prepare_route_feedback: ERROR: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
