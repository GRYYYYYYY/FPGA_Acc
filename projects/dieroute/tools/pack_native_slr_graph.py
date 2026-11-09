#!/usr/bin/env python3
"""Pack a native PIP neighbourhood for capacity/identity tests, never timing QoR."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import struct


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def pack(graph, prefix, connections, edge_identity=False):
    nodes, pips, wires = [rows(graph / (name + ".csv")) for name in ("nodes", "pips", "wires")]
    if not nodes or not pips or not connections:
        raise ValueError("empty graph or connection set")
    member_wires = [{} for _ in nodes]
    wire_owner = {}
    for w in wires:
        n, die = int(w["node_id"]), int(w["die"])
        identity = w["tile"], w["wire"]
        if n not in range(len(nodes)) or die not in range(8) or identity in wire_owner:
            raise ValueError("invalid or duplicate member wire")
        wire_owner[identity] = n
        member_wires[n][identity] = die
    membership, owners, boxes = [], [], []
    for n, row in enumerate(nodes):
        die, mask = int(row["owner_die"]), int(row["membership_mask"])
        actual = sum(1 << d for d in set(member_wires[n].values()))
        box = tuple(int(row[k]) for k in ("xlow", "ylow", "xhigh", "yhigh"))
        if (int(row["id"]) != n or die not in range(8) or not 0 < mask < 256 or mask != actual
                or member_wires[n].get((row["tile"], row["wire"])) != die
                or not all(0 <= x <= 65535 for x in box) or box[0] > box[2] or box[1] > box[3]):
            raise ValueError("node identity, membership or geometry mismatch")
        membership.append(mask); owners.append(die); boxes.append(box)
    adjacency = [[] for _ in nodes]
    seen, pip_identities = set(), set()
    for i, pip in enumerate(pips):
        identity = pip["tile"], pip["start_wire"], pip["end_wire"]
        if identity in pip_identities:
            raise ValueError("duplicate native PIP identity")
        pip_identities.add(identity)
        a, b, die = (int(pip[k]) for k in ("src", "dst", "die"))
        if (int(pip["id"]) != i or a not in range(len(nodes)) or b not in range(len(nodes))
                or die not in range(8) or pip["bidirectional"] not in ("true", "false")):
            raise ValueError("invalid PIP")
        for n, wire in ((a, pip["start_wire"]), (b, pip["end_wire"])):
            if member_wires[n].get((pip["tile"], wire)) != die:
                raise ValueError("PIP endpoint wire is not a member of its electrical node/die")
        arcs = [(a, b, False)] + ([(b, a, True)] if pip["bidirectional"] == "true" else [])
        for src, dst, reversed_pip in arcs:
            if (src, dst) in seen and not edge_identity:
                raise ValueError("parallel PIPs require edge identity in route output; unsupported here")
            seen.add((src, dst))
            adjacency[src].append((dst, die, i, reversed_pip))
    tasks = []
    roots, root_nets = {}, {}
    for i, (net, src, sink) in enumerate(connections):
        if (not 0 <= net < 0xffffffff or src not in range(len(nodes)) or sink not in range(len(nodes))
                or src == sink or membership[src].bit_count() != 1 or membership[sink].bit_count() != 1):
            raise ValueError("invalid task or ambiguous terminal access die")
        if roots.setdefault(net, src) != src:
            raise ValueError("a net must have one source")
        if root_nets.setdefault(src, net) != net or any(dst == src for _, dst in seen):
            raise ValueError("functional PR sources must be exclusive graph roots")
        tasks.append(struct.pack("<4I2H3I", i, net, src, sink, 0, 64, i, 0, 0))
    packed_nodes, packed_edges, packed_die, catalog = [], [], [], []
    for src, arcs in enumerate(adjacency):
        arcs.sort()
        if len(arcs) > 65535:
            raise ValueError("outdegree exceeds PR ABI")
        packed_nodes.append(struct.pack("<IHH", len(packed_edges), len(arcs), 0))
        for dst, die, pip_id, reverse in arcs:
            catalog.append({"edge_id": len(packed_edges), "src": src, "dst": dst,
                            "pip_id": pip_id, "reversed": reverse})
            packed_edges.append(struct.pack("<IHH", dst, 1, 0))
            packed_die.append(struct.pack("<H", die))
    payloads = {
        ".nodes": b"".join(packed_nodes), ".edges": b"".join(packed_edges),
        ".resources": struct.pack("<4H2I", 0, 1, 256, 0, 0, 0xffffffff) * len(nodes),
        ".tasks": b"".join(tasks), ".node_die": struct.pack("<" + "H" * len(owners), *owners),
        ".node_membership": struct.pack("<" + "H" * len(membership), *membership),
        ".edge_die": b"".join(packed_die), ".node_box": b"".join(struct.pack("<4H", *b) for b in boxes),
        ".edge_catalog.json": (json.dumps(catalog, indent=2) + "\n").encode(),
    }
    if edge_identity:
        if len(pips) > 2**31:
            raise ValueError("native PIP ID/direction key exceeds u32")
        payloads[".edge_ref"] = b"".join(struct.pack("<I", (e["pip_id"] << 1) | e["reversed"]) for e in catalog)
    destinations = [Path(str(prefix) + suffix) for suffix in [*payloads, ".native.json"]]
    if any(p.exists() for p in destinations):
        raise FileExistsError("output prefix already exists")
    prefix.parent.mkdir(parents=True, exist_ok=True)
    for suffix, data in payloads.items():
        with Path(str(prefix) + suffix).open("xb") as out:
            out.write(data)
    report = {"schema": "dieroute.native_pip_functional.v1", "board_result": False,
              "scope": "partial native graph, functional capacity/identity test only",
              "cost_model": "unit_base_zero_delay_no_timing_claim", "resource_capacity": 1,
              "occupancy_semantics": "PR counts route-tree child nodes; exclusive source terminals are not charged",
              "node_count": len(nodes), "edge_count": len(packed_edges), "connections": connections,
              "sidecar_encoding": "little-endian u16 membership masks and PIP SLR IDs; canonical node/CSR edge order",
              "edge_identity": edge_identity,
              "edge_ref_encoding": "u32 little-endian (catalog PIP ID << 1) | reversed" if edge_identity else None,
              "inputs": {str(graph / (n + ".csv")): sha(graph / (n + ".csv")) for n in ("nodes", "pips", "wires")},
              "artifacts": {str(p): sha(p) for p in destinations[:-1]}}
    with destinations[-1].open("x") as out:
        json.dump(report, out, indent=2); out.write("\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph", type=Path)
    parser.add_argument("prefix", type=Path)
    parser.add_argument("--connection", action="append", required=True, help="net_id,source_id,sink_id")
    parser.add_argument("--edge-identity", action="store_true", help="preserve parallel PIPs and emit immutable per-edge PIP keys")
    args = parser.parse_args()
    print(json.dumps(pack(args.graph, args.prefix, [tuple(map(int, s.split(","))) for s in args.connection], args.edge_identity)))
