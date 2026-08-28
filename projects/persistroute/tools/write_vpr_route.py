#!/usr/bin/env python3
"""Serialize PersistRoute route trees as a VPR-compatible text .route file.

The original VPR route supplies placement/header metadata, net ordering, and
the architecture/placement-dependent pin descriptions.  The RR graph supplies
descriptions for newly selected channel nodes and the switch on every edge.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


NET = re.compile(r"^\s*Net\s+(\d+)\s+\((.*)\)\s*$")
NODE = re.compile(r"^\s*Node:\s*(\d+)\s+(SOURCE|SINK|OPIN|IPIN|CHANX|CHANY)\b")
SWITCH = re.compile(r"^(.*?\bSwitch:)\s*-?\d+(?:\s+Net_pin_index:\s*(\d+))?\s*$")
PIN_TEXT = re.compile(r"\b(Pin|Pad):\s*(\d+)(?:\s+(\S+))?\s+Switch:$")
ARRAY_SIZE = re.compile(r"^Array size:\s*(\d+)\s*x\s*(\d+)\s+logic blocks\.$")


@dataclass(frozen=True)
class Node:
    kind: str
    xlow: int
    ylow: int
    xhigh: int
    yhigh: int
    layer: int
    ptc: int
    logical_pin: str | None = None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_original(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    starts = [i for i, line in enumerate(lines) if line.lstrip().startswith("Net ")]
    if len(lines) < 3 or not starts:
        raise ValueError(f"{path}: not a VPR route file")
    sections = []
    templates = {}
    pin_templates = {}
    routed = {}
    for pos, start in enumerate(starts):
        end = starts[pos + 1] if pos + 1 < len(starts) else len(lines)
        section = lines[start:end]
        match = NET.match(section[0])
        if match:
            net_id, name = int(match.group(1)), match.group(2)
            nodes = []
            for line in section[1:]:
                node_match = NODE.match(line)
                if not node_match:
                    continue
                node_id, kind = int(node_match.group(1)), node_match.group(2)
                switch_match = SWITCH.match(line)
                if not switch_match:
                    raise ValueError(f"cannot parse node line: {line}")
                prefix, pin = switch_match.group(1), switch_match.group(2)
                previous = templates.setdefault(node_id, prefix)
                if previous != prefix:
                    raise ValueError(f"RR node {node_id} has inconsistent text descriptions")
                nodes.append((node_id, kind, None if pin is None else int(pin)))
                pin_match = PIN_TEXT.search(prefix)
                if pin_match and kind in ("IPIN", "OPIN"):
                    key = (kind, pin_match.group(1), int(pin_match.group(2)))
                    value = pin_match.group(3)
                    old = pin_templates.setdefault(key, value)
                    if old != value:
                        pin_templates[key] = None
            routed[net_id] = {"name": name, "nodes": nodes, "section": section}
        sections.append((start, end, match, section))
    size_match = ARRAY_SIZE.match(lines[1])
    if not size_match:
        raise ValueError(f"{path}: cannot parse array dimensions")
    dimensions = (int(size_match.group(1)), int(size_match.group(2)))
    return lines, starts[0], sections, routed, templates, pin_templates, dimensions


def load_connections(path: Path, original):
    by_net = defaultdict(list)
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            by_net[int(row["net_id"])].append(row)
    for net_id, rows in by_net.items():
        if net_id not in original:
            raise ValueError(f"connections reference absent net {net_id}")
        observed = [(n, pin) for n, kind, pin in original[net_id]["nodes"] if kind == "SINK"]
        expected = [int(row["sink"]) for row in rows]
        if [node for node, _ in observed] != expected:
            raise ValueError(f"net {net_id}: connection sink order differs from original route")
        if any(pin is None for _, pin in observed):
            raise ValueError(f"net {net_id}: original SINK lacks Net_pin_index")
        for row, (_, pin) in zip(rows, observed):
            row["net_pin_index"] = pin
    return by_net


def load_trees(path: Path):
    edges = defaultdict(list)
    sources = {}
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            net_id = int(row["net_id"])
            source, parent, child = int(row["source"]), int(row["parent"]), int(row["child"])
            if net_id in sources and sources[net_id] != source:
                raise ValueError(f"net {net_id}: inconsistent sources")
            sources[net_id] = source
            edges[net_id].append((parent, child))
    return edges, sources


def load_rr_graph(path: Path, used_nodes: set[int], used_edges: set[tuple[int, int]]):
    nodes = {}
    edge_switch = {}
    ambiguous = {}
    block_pins = {}
    grid = {}
    for _, elem in ET.iterparse(path, events=("end",)):
        tag = elem.tag.rsplit("}", 1)[-1]
        if tag == "block_type":
            block_pins[int(elem.attrib["id"])] = {
                int(pin.attrib["ptc"]): (pin.text or "")
                for pin in elem.iter() if pin.tag.rsplit("}", 1)[-1] == "pin"
            }
            elem.clear()
        elif tag == "grid_loc":
            a = elem.attrib
            grid[(int(a["x"]), int(a["y"]), int(a.get("layer", 0)))] = int(a["block_type_id"])
            elem.clear()
        elif tag == "node":
            node_id = int(elem.attrib["id"])
            if node_id in used_nodes:
                loc = next(child for child in elem if child.tag.rsplit("}", 1)[-1] == "loc")
                a = loc.attrib
                coordinate = (int(a["xlow"]), int(a["ylow"]), int(a.get("layer", 0)))
                ptc = int(a["ptc"])
                block_type = grid.get(coordinate)
                nodes[node_id] = Node(
                    elem.attrib["type"], int(a["xlow"]), int(a["ylow"]),
                    int(a["xhigh"]), int(a["yhigh"]), int(a.get("layer", 0)), ptc,
                    block_pins.get(block_type, {}).get(ptc),
                )
            elem.clear()
        elif tag == "edge":
            pair = (int(elem.attrib["src_node"]), int(elem.attrib["sink_node"]))
            if pair in used_edges:
                switch = int(elem.attrib["switch_id"])
                if pair not in edge_switch:
                    edge_switch[pair] = switch
                elif edge_switch[pair] != switch:
                    ambiguous.setdefault(pair, {edge_switch[pair]}).add(switch)
            elem.clear()
    missing_nodes = used_nodes - nodes.keys()
    missing_edges = used_edges - edge_switch.keys()
    if missing_nodes:
        raise ValueError(f"RR graph missing used nodes: {sorted(missing_nodes)[:8]}")
    if missing_edges:
        raise ValueError(f"RR graph missing used edges: {sorted(missing_edges)[:8]}")
    return nodes, edge_switch, ambiguous


def validate_tree(net_id, source, edges, sinks):
    parent = {}
    children = defaultdict(list)
    for a, b in edges:
        if a == b:
            raise ValueError(f"net {net_id}: self edge at {a}")
        if b in parent and parent[b] != a:
            raise ValueError(f"net {net_id}: node {b} has two parents")
        parent[b] = a
        children[a].append(b)
    if source in parent:
        raise ValueError(f"net {net_id}: source {source} has a parent")
    paths = []
    reachable = {source}
    stack = [source]
    while stack:
        node = stack.pop()
        for child in children[node]:
            if child in reachable:
                raise ValueError(f"net {net_id}: cycle or reconvergence at {child}")
            reachable.add(child)
            stack.append(child)
    edge_nodes = {node for edge in edges for node in edge}
    if edge_nodes - reachable:
        raise ValueError(f"net {net_id}: disconnected tree nodes")
    for sink in sinks:
        if sink not in reachable:
            raise ValueError(f"net {net_id}: sink {sink} is unreachable")
        path = [sink]
        while path[-1] != source:
            if path[-1] not in parent:
                raise ValueError(f"net {net_id}: broken parent chain for sink {sink}")
            path.append(parent[path[-1]])
        paths.append(list(reversed(path)))
    leaves = {node for node in reachable if not children[node]}
    if leaves != set(sinks):
        raise ValueError(f"net {net_id}: leaves differ from terminal SINKs")
    return paths


def node_prefix(node_id: int, node: Node, templates, pin_templates, dimensions) -> str:
    if node_id in templates:
        return templates[node_id]
    if node.kind not in ("CHANX", "CHANY", "IPIN", "OPIN"):
        raise ValueError(f"new {node.kind} node {node_id} has no original pin/class description")
    text = f"Node: {node_id} {node.kind} ({node.xlow},{node.ylow},{node.layer}) "
    if node.xlow != node.xhigh or node.ylow != node.yhigh:
        text += f"to ({node.xhigh},{node.yhigh},{node.layer}) "
    if node.kind in ("CHANX", "CHANY"):
        return text + f"Track: {node.ptc} Switch:"
    width, height = dimensions
    marker = "Pad" if node.xlow in (0, width - 1) or node.ylow in (0, height - 1) else "Pin"
    key = (node.kind, marker, node.ptc)
    if node.logical_pin is not None:
        logical = node.logical_pin
    elif key not in pin_templates or pin_templates[key] is None:
        raise ValueError(f"new {node.kind} node {node_id} has no learned logical pin description for {key}")
    else:
        logical = pin_templates[key]
    logical_text = f" {logical}" if logical else ""
    return text + f"{marker}: {node.ptc}{logical_text} Switch:"


def serialize_net(net_id, name, source, edge_rows, connections, nodes, switches, templates, pin_templates, dimensions):
    sinks = [int(row["sink"]) for row in connections]
    paths = validate_tree(net_id, source, edge_rows, sinks)
    trace = []
    emitted = set()
    for path, row in zip(paths, connections):
        if not emitted:
            start = 0
        else:
            common = [i for i, node in enumerate(path[:-1]) if node in emitted]
            if not common:
                raise ValueError(f"net {net_id}: no emitted branch point for sink {row['sink']}")
            start = max(common)
        suffix = path[start:]
        for index, node_id in enumerate(suffix):
            outgoing = switches[(node_id, suffix[index + 1])] if index + 1 < len(suffix) else -1
            pin = f" Net_pin_index: {row['net_pin_index']}" if index + 1 == len(suffix) else ""
            trace.append(f"{node_prefix(node_id, nodes[node_id], templates, pin_templates, dimensions)} {outgoing}{pin}")
        emitted.update(path)
    return [f"Net {net_id} ({name})", "", *trace, ""]


def write_route(original_route: Path, rr_graph: Path, connections_path: Path, trees_path: Path, output: Path):
    lines, prefix_end, sections, original, templates, pin_templates, dimensions = parse_original(original_route)
    connections = load_connections(connections_path, original)
    trees, sources = load_trees(trees_path)
    if set(trees) != set(connections):
        raise ValueError(f"tree/connection net sets differ: {len(trees)} versus {len(connections)}")
    used_edges = {edge for rows in trees.values() for edge in rows}
    used_nodes = {node for edge in used_edges for node in edge} | set(sources.values())
    nodes, switches, ambiguous = load_rr_graph(rr_graph, used_nodes, used_edges)
    generated = {}
    for net_id, rows in connections.items():
        source = sources[net_id]
        if any(int(row["source"]) != source for row in rows):
            raise ValueError(f"net {net_id}: task source differs from tree source")
        generated[net_id] = serialize_net(
            net_id, original[net_id]["name"], source, trees[net_id], rows,
            nodes, switches, templates, pin_templates, dimensions,
        )
    out_lines = lines[:prefix_end]
    for _, _, match, section in sections:
        net_id = int(match.group(1)) if match else None
        out_lines.extend(generated.get(net_id, section))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(out_lines).rstrip() + "\n", encoding="utf-8")
    return {
        "original_route": str(original_route.resolve()),
        "original_route_sha256": sha256(original_route),
        "rr_graph_sha256": sha256(rr_graph),
        "connections_sha256": sha256(connections_path),
        "route_trees_sha256": sha256(trees_path),
        "output": str(output.resolve()),
        "output_sha256": sha256(output),
        "routed_nets": len(generated),
        "connections": sum(map(len, connections.values())),
        "tree_edges": len(used_edges),
        "ambiguous_used_rr_edges": len(ambiguous),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("original_route", type=Path)
    parser.add_argument("rr_graph", type=Path)
    parser.add_argument("connections", type=Path)
    parser.add_argument("route_trees", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(write_route(args.original_route, args.rr_graph, args.connections, args.route_trees, args.output), indent=2))


if __name__ == "__main__":
    main()
