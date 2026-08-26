#!/usr/bin/env python3
"""Convert VPR 9 rr_graph.xml to a deterministic FPGA-Acc binary graph."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

MAGIC = b"FPRRGR01"
HEADER = struct.Struct("<8sIIIIQQQQ")
NODE = struct.Struct("<IHHHHHHHHff")
EDGE = struct.Struct("<IIHHI")
TYPE = {"SOURCE": 0, "SINK": 1, "IPIN": 2, "OPIN": 3, "CHANX": 4, "CHANY": 5}
DIRECTION = {"NONE": 0, "INC_DIR": 1, "DEC_DIR": 2, "BI_DIR": 3, "INC": 1, "DEC": 2, "BI": 3}


def attr_int(elem, name, default=0):
    return int(elem.attrib.get(name, default))


def attr_float(elem, name, default=0.0):
    return float(elem.attrib.get(name, default))


def convert(xml_path: Path, out_path: Path, meta_path: Path) -> dict:
    root = ET.parse(xml_path).getroot()
    switches = {}
    for switch in root.findall("./switches/switch"):
        timing = switch.find("timing")
        switches[attr_int(switch, "id")] = attr_float(timing, "Tdel") if timing is not None else 0.0

    nodes = []
    for node in root.findall("./rr_nodes/node"):
        loc = node.find("loc")
        timing = node.find("timing")
        segment = node.find("segment")
        if loc is None:
            raise ValueError(f"node {node.attrib.get('id')} has no loc")
        nodes.append({
            "id": attr_int(node, "id"),
            "type": TYPE.get(node.attrib.get("type", ""), 65535),
            "direction": DIRECTION.get(node.attrib.get("direction", "NONE"), 0),
            "capacity": attr_int(node, "capacity", 1),
            "xlow": attr_int(loc, "xlow"), "ylow": attr_int(loc, "ylow"),
            "xhigh": attr_int(loc, "xhigh"), "yhigh": attr_int(loc, "yhigh"),
            "ptc": attr_int(loc, "ptc"),
            "segment": attr_int(segment, "segment_id", 65535) if segment is not None else 65535,
            "R": attr_float(timing, "R") if timing is not None else 0.0,
            "C": attr_float(timing, "C") if timing is not None else 0.0,
        })
    nodes.sort(key=lambda item: item["id"])
    for expected, node in enumerate(nodes):
        if node["id"] != expected:
            raise ValueError(f"node IDs must be dense: expected {expected}, got {node['id']}")

    raw_edges = []
    degrees = [0] * len(nodes)
    for edge in root.findall("./rr_edges/edge"):
        src, dst, switch = attr_int(edge, "src_node"), attr_int(edge, "sink_node"), attr_int(edge, "switch_id")
        if src >= len(nodes) or dst >= len(nodes):
            raise ValueError(f"edge outside node range: {src}->{dst}")
        raw_edges.append((src, dst, switch))
        degrees[src] += 1
    raw_edges.sort()
    offsets = [0] * (len(nodes) + 1)
    for index, degree in enumerate(degrees):
        offsets[index + 1] = offsets[index] + degree

    with out_path.open("wb") as output:
        edge_offset = HEADER.size + len(nodes) * NODE.size
        output.write(HEADER.pack(MAGIC, 1, len(nodes), len(raw_edges), len(switches), HEADER.size, edge_offset, 0, 0))
        for node in nodes:
            output.write(NODE.pack(offsets[node["id"]], degrees[node["id"]], node["type"], node["direction"],
                                   node["capacity"], node["xlow"], node["ylow"], node["xhigh"], node["yhigh"],
                                   node["R"], node["C"]))
        for src, dst, switch in raw_edges:
            delay_q = max(0, min(65535, round(switches.get(switch, 0.0) * 1e12)))
            output.write(EDGE.pack(src, dst, switch, nodes[dst]["segment"], delay_q))

    metadata = {
        "schema": "FPRRGR01", "source": str(xml_path.resolve()),
        "source_sha256": hashlib.sha256(xml_path.read_bytes()).hexdigest(),
        "binary_sha256": hashlib.sha256(out_path.read_bytes()).hexdigest(),
        "nodes": len(nodes), "edges": len(raw_edges), "switches": len(switches),
        "node_bytes": NODE.size, "edge_bytes": EDGE.size,
        "switch_tdel_seconds": switches, "type_encoding": TYPE, "direction_encoding": DIRECTION,
    }
    meta_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return metadata


def validate(path: Path) -> dict:
    data = path.read_bytes()
    magic, version, nodes, edges, switches, node_offset, edge_offset, _, _ = HEADER.unpack_from(data)
    if magic != MAGIC or version != 1:
        raise ValueError("bad graph header")
    expected_size = edge_offset + edges * EDGE.size
    if len(data) != expected_size:
        raise ValueError(f"size mismatch {len(data)} != {expected_size}")
    previous = 0
    for index in range(nodes):
        offset, count, *_ = NODE.unpack_from(data, node_offset + index * NODE.size)
        if offset < previous or offset + count > edges:
            raise ValueError(f"bad CSR at node {index}")
        previous = offset
    for index in range(edges):
        src, dst, _, _, _ = EDGE.unpack_from(data, edge_offset + index * EDGE.size)
        if src >= nodes or dst >= nodes:
            raise ValueError(f"bad edge {index}")
    return {"valid": True, "nodes": nodes, "edges": edges, "switches": switches,
            "sha256": hashlib.sha256(data).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path, nargs="?")
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        print(json.dumps(validate(args.input), indent=2))
        return
    if args.output is None:
        parser.error("output is required unless --validate-only is used")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    metadata_path = args.metadata or args.output.with_suffix(args.output.suffix + ".json")
    converted = convert(args.input, args.output, metadata_path)
    checked = validate(args.output)
    if converted["nodes"] != checked["nodes"] or converted["edges"] != checked["edges"]:
        raise SystemExit("round-trip count mismatch")
    print(json.dumps(checked, indent=2))


if __name__ == "__main__":
    main()
