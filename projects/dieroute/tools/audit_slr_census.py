#!/usr/bin/env python3
"""Audit the native LAG_LAG-node diagnostic; this does not certify SLL capacity."""
import argparse
from collections import Counter
import csv
import hashlib
import itertools
import json
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit(manifest):
    data = json.loads(manifest.read_text())
    if data["status"] != "passed" or data["probe_exit_code"] != 0:
        raise ValueError("native census did not succeed")
    base = manifest.parent
    for name, expected in data["artifacts"].items():
        if sha256(base / name) != expected:
            raise ValueError("artifact hash mismatch: " + name)
    for name, expected in data["device_data"].items():
        if sha256(Path(data["runtime"]) / name) != expected:
            raise ValueError("native device hash mismatch: " + name)
    keys = set()
    intents, memberships = Counter(), Counter()
    total_wires = 0
    examples = []
    def identity(row):
        return row["canonical_tile"], row["canonical_wire"]
    with (base / "census/nodes.csv").open() as nf, (base / "census/wires.csv").open() as wf:
        nodes = csv.DictReader(nf)
        groups = itertools.groupby(csv.DictReader(wf), identity)
        for node, group in itertools.zip_longest(nodes, groups):
            if node is None or group is None:
                raise ValueError("node/wire group counts differ")
            key = identity(node)
            if key in keys or key != group[0]:
                raise ValueError("duplicate or mismatched canonical node")
            keys.add(key)
            seen_wires = set()
            actual_slrs = set()
            canonical_slr = None
            for wire in group[1]:
                member = wire["member_tile"], wire["member_wire"]
                if member in seen_wires:
                    raise ValueError("duplicate member wire")
                seen_wires.add(member)
                slr = int(wire["member_slr"])
                if slr < 0:
                    raise ValueError("unknown native SLR")
                actual_slrs.add(slr)
                if member == key:
                    canonical_slr = slr
            declared = ";".join(map(str, sorted(actual_slrs)))
            if (declared != node["member_slrs"] or canonical_slr != int(node["representative_slr"])
                    or len(seen_wires) != int(node["wire_count"])):
                raise ValueError("node summary disagrees with wire-level evidence")
            total_wires += len(seen_wires)
            if len(actual_slrs) > 1:
                intents[node["intent"]] += 1
                memberships[declared] += 1
                if len(examples) < 5:
                    examples.append(node)
    return {
        "schema": "dieroute.audited_slr_census.v1",
        "manifest": str(manifest), "manifest_sha256": sha256(manifest),
        "scope": data["scope"], "board_result": False,
        "unique_electrical_nodes": len(keys), "member_wires": total_wires,
        "multi_slr_nodes": sum(intents.values()),
        "multi_slr_by_intent": dict(sorted(intents.items())),
        "multi_slr_by_membership": dict(sorted(memberships.items())),
        "examples": examples,
        "limitations": ["Partial device census, not a complete routing graph",
                        "Membership counts do not establish independent SLL capacity",
                        "No routed design or DCP round-trip validation",
                        "No physical board execution"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = audit(args.manifest.resolve())
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({key: result[key] for key in
          ("unique_electrical_nodes", "member_wires", "multi_slr_nodes")}))
