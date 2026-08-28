#!/usr/bin/env python3
"""Pack a VPR rr_graph.xml and connection CSV for PersistRoute/XRT.

The emitted files are raw little-endian arrays matching persistroute.hpp.  A
manifest records exact element counts, byte sizes and hashes so the host never
has to infer a schema from a filename.
"""
from __future__ import annotations

import argparse
from array import array
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


def _write_array(path: Path, rows, record: struct.Struct) -> dict:
    digest = hashlib.sha256()
    count = 0
    with path.open("wb") as stream:
        for row in rows:
            packed = record.pack(*row)
            stream.write(packed)
            digest.update(packed)
            count += 1
    return {"path": path.name, "count": count, "record_bytes": record.size,
            "bytes": count * record.size, "sha256": digest.hexdigest()}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def pack(rr_graph: Path, connections: Path, prefix: Path, base_cost_q: int,
         channel_length_cost_q: int = 0) -> dict:
    switch_timing: dict[int, tuple[float, float, bool]] = {}
    node_r, node_c = array("d"), array("d")
    node_wirelength, node_capacity = array("H"), array("H")
    stack = []
    for event, elem in ET.iterparse(rr_graph, events=("start", "end")):
        if event == "start":
            stack.append(elem)
            continue
        tag = elem.tag.rsplit("}", 1)[-1]
        if tag == "switch":
            timing = elem.find("timing")
            buffered = elem.attrib.get("type", "mux") not in {"pass_gate", "short"}
            switch_timing[_integer(elem, "id")] = (
                _floating(timing, "Tdel"), _floating(timing, "R"), buffered)
        elif tag == "node":
            expected = len(node_r)
            if _integer(elem, "id") != expected:
                raise ValueError("PersistRoute requires dense zero-based rr node IDs")
            timing, loc = elem.find("timing"), elem.find("loc")
            node_r.append(_floating(timing, "R"))
            node_c.append(_floating(timing, "C"))
            if elem.attrib.get("type") in {"CHANX", "CHANY"} and loc is not None:
                length = max(_integer(loc, "xhigh") - _integer(loc, "xlow"),
                             _integer(loc, "yhigh") - _integer(loc, "ylow")) + 1
                node_wirelength.append(length)
            else:
                node_wirelength.append(0)
            node_capacity.append(max(1, min(65535, _integer(elem, "capacity", 1))))
        if tag in {"switch", "node"} and len(stack) >= 2:
            stack[-2].remove(elem)
            elem.clear()
        stack.pop()
        if tag == "rr_nodes":
            break

    node_count = len(node_r)
    edge_begin, edge_counts = array("I", [0]) * node_count, array("I", [0]) * node_count
    edge_path = prefix.with_suffix(".edges")
    edge_digest, edge_total, cursor = hashlib.sha256(), 0, 0
    current_src, outgoing = None, []

    def flush_edges(stream) -> None:
        nonlocal outgoing, cursor, edge_total
        if current_src is None:
            return
        outgoing.sort(key=lambda item: (item[0], item[2], item[1]))
        if len(outgoing) > 65535:
            raise ValueError(f"node {current_src} fanout exceeds uint16")
        edge_begin[current_src], edge_counts[current_src] = cursor, len(outgoing)
        for row in outgoing:
            packed = EDGE.pack(*row)
            stream.write(packed)
            edge_digest.update(packed)
        cursor += len(outgoing)
        edge_total += len(outgoing)
        outgoing = []

    prefix.parent.mkdir(parents=True, exist_ok=True)
    stack = []
    with edge_path.open("wb") as edge_stream:
        for event, elem in ET.iterparse(rr_graph, events=("start", "end")):
            if event == "start":
                stack.append(elem)
                continue
            tag = elem.tag.rsplit("}", 1)[-1]
            if tag == "edge":
                src, dst, switch = (_integer(elem, name) for name in
                                    ("src_node", "sink_node", "switch_id"))
                if src >= node_count or dst >= node_count:
                    raise ValueError(f"edge outside node range: {src}->{dst}")
                if current_src is not None and src < current_src:
                    raise ValueError("PersistRoute streaming pack requires RR edges grouped by source")
                if current_src is None or src != current_src:
                    flush_edges(edge_stream)
                    current_src = src
                tdel, switch_r, buffered = switch_timing.get(switch, (0.0, 0.0, True))
                if buffered:
                    local_delay = tdel + switch_r * node_c[dst] + 0.5 * node_r[dst] * node_c[dst]
                else:
                    local_delay = tdel + 0.5 * switch_r * node_c[dst]
                delay_q = max(0, min(65535, round(local_delay * 1e12)))
                length = max(1, node_wirelength[dst])
                edge_base_cost = base_cost_q + channel_length_cost_q * (length - 1)
                if edge_base_cost > 65535:
                    raise ValueError(f"edge base cost exceeds uint16 for {src}->{dst}")
                outgoing.append((dst, edge_base_cost, delay_q))
            if tag in {"node", "edge"} and len(stack) >= 2:
                stack[-2].remove(elem)
                elem.clear()
            stack.pop()
            if tag == "rr_edges":
                break
        flush_edges(edge_stream)

    cursor = 0
    for node_id in range(node_count):
        edge_begin[node_id] = cursor
        cursor += edge_counts[node_id]

    edge_file = {"path": edge_path.name, "count": edge_total, "record_bytes": EDGE.size,
                 "bytes": edge_total * EDGE.size, "sha256": edge_digest.hexdigest()}

    tasks: list[tuple[int, int, int, int, int, int, int]] = []
    with connections.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"id", "net_id", "source", "sink", "criticality_q", "max_hops", "priority", "epoch"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"connection CSV must contain {sorted(required)}")
        for row in reader:
            values = tuple(int(row[name], 0) for name in
                           ("id", "net_id", "source", "sink", "criticality_q", "max_hops", "priority", "epoch")) + (0,)
            if values[2] >= node_count or values[3] >= node_count:
                raise ValueError(f"task {values[0]} source/sink outside graph")
            if values[4] > 65535 or values[5] > 65535:
                raise ValueError(f"task {values[0]} has uint16 overflow")
            tasks.append(values)
    tasks.sort(key=lambda item: (item[6], item[0]))

    files = {
        "nodes": _write_array(prefix.with_suffix(".nodes"),
                              ((edge_begin[i], edge_counts[i], node_wirelength[i])
                               for i in range(node_count)), NODE),
        "edges": edge_file,
        "resources": _write_array(prefix.with_suffix(".resources"),
                                  ((0, node_capacity[i], 256, 0, 0, 0xFFFFFFFF)
                                   for i in range(node_count)), RESOURCE),
        "tasks": _write_array(prefix.with_suffix(".tasks"), tasks, TASK),
    }
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "endianness": "little",
        "rr_graph": str(rr_graph.resolve()),
        "rr_graph_sha256": _sha256(rr_graph),
        "connections": str(connections.resolve()),
        "connections_sha256": _sha256(connections),
        "base_cost_q": base_cost_q,
        "channel_length_cost_q": channel_length_cost_q,
        "wirelength_cost_model": "base_cost_q + channel_length_cost_q * (destination RR channel length - 1)",
        "node_delay_class_semantics": "VPR RR channel wirelength; zero for non-channel nodes",
        "edge_delay_model": "VPR buffered local T_linear (ps), pass switch local RC approximation",
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
    parser.add_argument("--channel-length-cost-q", type=int, default=0)
    args = parser.parse_args()
    if not 0 <= args.base_cost_q <= 65535 or not 0 <= args.channel_length_cost_q <= 65535:
        parser.error("edge cost fields must fit uint16")
    print(json.dumps(pack(args.rr_graph, args.connections, args.output_prefix,
                          args.base_cost_q, args.channel_length_cost_q), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
