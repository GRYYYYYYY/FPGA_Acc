#!/usr/bin/env python3
"""Export explicit VPR layer ownership without inventing physical SLL capacity.

This is a format converter, not a routing algorithm. Cross-layer edges are not
independent SLLs: several edges may consume the same destination RR resource.
The C++ router must enforce the original per-node capacity and net sharing.
"""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import struct
import xml.etree.ElementTree as ET

from run_native_case import sha256


def export(rr_graph, prefix, connections=None):
    owners, capacities, types, boxes = [], [], [], []
    cuts = Counter()
    stack = []
    prefix.parent.mkdir(parents=True, exist_ok=True)
    crossing_path = Path(str(prefix) + ".crossings.csv")
    owner_path = Path(str(prefix) + ".node_die")
    box_path = Path(str(prefix) + ".node_box")
    for path in (crossing_path, owner_path, box_path, Path(str(prefix) + ".topology.json")):
        if path.exists():
            raise FileExistsError(path)
    with crossing_path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["src", "dst", "src_die", "dst_die", "switch_id", "dst_capacity"])
        for event, elem in ET.iterparse(rr_graph, events=("start", "end")):
            if event == "start":
                stack.append(elem)
                continue
            tag = elem.tag
            if tag == "node":
                if int(elem.attrib["id"]) != len(owners):
                    raise ValueError("node IDs must be dense and zero-based")
                loc = elem.find("loc")
                if loc is None or "layer" not in loc.attrib:
                    raise ValueError("explicit loc.layer is required; do not infer dies from XY")
                layer, capacity = int(loc.attrib["layer"]), int(elem.attrib["capacity"])
                if not 0 <= layer < 65535 or not 1 <= capacity <= 65535:
                    raise ValueError("layer/capacity outside sidecar/PR ABI")
                owners.append(layer)
                capacities.append(capacity)
                types.append(elem.attrib["type"])
                box = tuple(int(loc.attrib[k]) for k in ("xlow", "ylow", "xhigh", "yhigh"))
                if not all(0 <= n <= 65535 for n in box) or box[0] > box[2] or box[1] > box[3]:
                    raise ValueError("invalid RR node geometry")
                boxes.append(box)
            elif tag == "edge":
                src, dst, switch = (int(elem.attrib[key]) for key in ("src_node", "sink_node", "switch_id"))
                if min(src, dst) < 0 or max(src, dst) >= len(owners):
                    raise ValueError("edge references unknown RR node")
                if owners[src] != owners[dst]:
                    writer.writerow([src, dst, owners[src], owners[dst], switch, capacities[dst]])
                    cuts[(owners[src], owners[dst])] += 1
            if tag in {"node", "edge", "grid_loc", "block_type", "switch"} and len(stack) >= 2:
                stack[-2].remove(elem)
                elem.clear()
            stack.pop()
    layers = sorted(set(owners))
    if len(layers) < 2 or not cuts:
        raise ValueError("not a connected multi-layer RR topology")
    if layers != list(range(len(layers))):
        raise ValueError("die IDs must be dense and zero-based")
    with owner_path.open("wb") as stream:
        for owner in owners:
            stream.write(struct.pack("<H", owner))
    with box_path.open("wb") as stream:
        for box in boxes:
            stream.write(struct.pack("<4H", *box))
    report = {"schema": "dieroute.vpr_topology.v2", "rr_graph_sha256": sha256(rr_graph),
              "node_count": len(owners), "die_count": len(layers),
              "nodes_by_die": {str(k): v for k, v in sorted(Counter(owners).items())},
              "crossings": [{"src_die": a, "dst_die": b, "rr_edge_count": n}
                            for (a, b), n in sorted(cuts.items())],
              "capacity_semantics": "original RR node capacity; crossing edge count is NOT SLL capacity",
              "node_die_encoding": "little-endian uint16, dense RR node ID order",
              "node_box_encoding": "little-endian 4 x uint16: xlow,ylow,xhigh,yhigh; dense RR node ID order",
              "artifacts": {str(f): {"sha256": sha256(f), "bytes": f.stat().st_size}
                            for f in (owner_path, crossing_path, box_path)}}
    if connections:
        with connections.open() as stream:
            tasks = list(csv.DictReader(stream))
        cross = 0
        for task in tasks:
            src, dst = int(task["source"]), int(task["sink"])
            if min(src, dst) < 0 or max(src, dst) >= len(owners):
                raise ValueError("task references unknown node")
            if types[src] != "SOURCE" or types[dst] != "SINK":
                raise ValueError("task endpoints must be SOURCE/SINK")
            cross += owners[src] != owners[dst]
        report["tasks"] = {"count": len(tasks), "cross_die_endpoints": cross,
                           "connections_sha256": sha256(connections)}
    Path(str(prefix) + ".topology.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("rr_graph", type=Path)
    p.add_argument("prefix", type=Path)
    p.add_argument("--connections", type=Path)
    a = p.parse_args()
    print(json.dumps(export(a.rr_graph, a.prefix, a.connections), indent=2))
