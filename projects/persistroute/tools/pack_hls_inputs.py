#!/usr/bin/env python3
"""Pack a VPR rr_graph.xml and connection CSV for PersistRoute/XRT.

The emitted files are raw little-endian arrays matching persistroute.hpp.  A
manifest records exact element counts, byte sizes and hashes so the host never
has to infer a schema from a filename.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

NODE = struct.Struct("<IHH")
EDGE = struct.Struct("<IHH")
RESOURCE = struct.Struct("<HHHHII")
TASK = struct.Struct("<IIIIHHIII")
MANIFEST_SCHEMA = "PERSISTROUTE_XRT_INPUT_V1"


def _integer(element: ET.Element, name: str, default: int = 0) -> int:
    return int(element.attrib.get(name, default))


def _floating(element: ET.Element | None, name: str, default: float = 0.0) -> float:
    return float(element.attrib.get(name, default)) if element is not None else default


def _write_array(path: Path, rows: list[tuple], record: struct.Struct) -> dict:
    digest = hashlib.sha256()
    with path.open("wb") as stream:
        for row in rows:
            packed = record.pack(*row)
            stream.write(packed)
            digest.update(packed)
    return {"path": path.name, "count": len(rows), "record_bytes": record.size,
            "bytes": len(rows) * record.size, "sha256": digest.hexdigest()}


def pack(rr_graph: Path, connections: Path, prefix: Path, base_cost_q: int) -> dict:
    root = ET.parse(rr_graph).getroot()
    switch_delay = {}
    for switch in root.findall("./switches/switch"):
        switch_delay[_integer(switch, "id")] = _floating(switch.find("timing"), "Tdel")

    xml_nodes = sorted(root.findall("./rr_nodes/node"), key=lambda n: _integer(n, "id"))
    for expected, node in enumerate(xml_nodes):
        if _integer(node, "id") != expected:
            raise ValueError("PersistRoute requires dense zero-based rr node IDs")

    grouped: list[list[tuple[int, int, int]]] = [[] for _ in xml_nodes]
    for edge in root.findall("./rr_edges/edge"):
        src = _integer(edge, "src_node")
        dst = _integer(edge, "sink_node")
        switch = _integer(edge, "switch_id")
        if src >= len(grouped) or dst >= len(grouped):
            raise ValueError(f"edge outside node range: {src}->{dst}")
        delay_q = max(0, min(65535, round(switch_delay.get(switch, 0.0) * 1e12)))
        grouped[src].append((dst, base_cost_q, delay_q))

    nodes: list[tuple[int, int, int]] = []
    edges: list[tuple[int, int, int]] = []
    resources: list[tuple[int, int, int, int, int, int]] = []
    cursor = 0
    for node_id, xml_node in enumerate(xml_nodes):
        outgoing = sorted(grouped[node_id], key=lambda item: (item[0], item[2], item[1]))
        if len(outgoing) > 65535:
            raise ValueError(f"node {node_id} fanout exceeds uint16")
        nodes.append((cursor, len(outgoing), 0))
        edges.extend(outgoing)
        cursor += len(outgoing)
        capacity = max(1, min(65535, _integer(xml_node, "capacity", 1)))
        resources.append((0, capacity, 256, 0, 0, 0xFFFFFFFF))

    tasks: list[tuple[int, int, int, int, int, int, int]] = []
    with connections.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"id", "net_id", "source", "sink", "criticality_q", "max_hops", "priority", "epoch"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"connection CSV must contain {sorted(required)}")
        for row in reader:
            values = tuple(int(row[name], 0) for name in
                           ("id", "net_id", "source", "sink", "criticality_q", "max_hops", "priority", "epoch")) + (0,)
            if values[2] >= len(nodes) or values[3] >= len(nodes):
                raise ValueError(f"task {values[0]} source/sink outside graph")
            if values[4] > 65535 or values[5] > 65535:
                raise ValueError(f"task {values[0]} has uint16 overflow")
            tasks.append(values)
    tasks.sort(key=lambda item: (item[6], item[0]))

    prefix.parent.mkdir(parents=True, exist_ok=True)
    files = {
        "nodes": _write_array(prefix.with_suffix(".nodes"), nodes, NODE),
        "edges": _write_array(prefix.with_suffix(".edges"), edges, EDGE),
        "resources": _write_array(prefix.with_suffix(".resources"), resources, RESOURCE),
        "tasks": _write_array(prefix.with_suffix(".tasks"), tasks, TASK),
    }
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "endianness": "little",
        "rr_graph": str(rr_graph.resolve()),
        "rr_graph_sha256": hashlib.sha256(rr_graph.read_bytes()).hexdigest(),
        "connections": str(connections.resolve()),
        "connections_sha256": hashlib.sha256(connections.read_bytes()).hexdigest(),
        "base_cost_q": base_cost_q,
        "files": files,
        "kernel": "search_hbm_kernel",
        "production_limits": {"node_id": "uint32", "edge_index": "uint32", "task_count": "uint32", "path_length": "uint16"},
        "legacy_on_chip_kernel_limits": {"max_resources": 8192, "max_edges": 65536, "max_tasks": 1024},
    }
    manifest_path = Path(str(prefix) + ".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("rr_graph", type=Path)
    parser.add_argument("connections", type=Path)
    parser.add_argument("output_prefix", type=Path)
    parser.add_argument("--base-cost-q", type=int, default=256)
    args = parser.parse_args()
    print(json.dumps(pack(args.rr_graph, args.connections, args.output_prefix,
                          args.base_cost_q), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
