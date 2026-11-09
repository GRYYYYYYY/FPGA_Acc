#!/usr/bin/env python3
"""Compare full leaf/top connectivity; permit only isolated constant deletion.

Never merge static nets or discard floating input/output bits. This checks an
EDIF abstraction with primitive/opaque boundaries, not encrypted cell internals.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from run_native_case import sha256


def ordered_rows(path, field):
    previous = None
    with path.open() as stream:
        for row in csv.DictReader(stream):
            key = row[field]
            if previous is not None and key.encode("utf-16-be") <= previous.encode("utf-16-be"):
                raise ValueError("duplicate or unsorted identity: " + str(path))
            previous = key
            yield row


def compare_rows(left, right, key, diff_file):
    ai, bi = iter(ordered_rows(left, key)), iter(ordered_rows(right, key))
    a, b = next(ai, None), next(bi, None)
    removed, added, changes = [], [], []
    same = changed = 0
    with diff_file.open("w") as output:
        while a is not None or b is not None:
            if b is None or (a is not None and a[key] != b[key] and a[key].encode("utf-16-be") < b[key].encode("utf-16-be")):
                removed.append(a)
                output.write(json.dumps({"removed": a}) + "\n")
                a = next(ai, None)
                continue
            if a is None or a[key] != b[key]:
                added.append(b)
                output.write(json.dumps({"added": b}) + "\n")
                b = next(bi, None)
                continue
            if a == b:
                same += 1
            else:
                changed += 1
                entry = {"identity": a[key], "differences": {k: [a[k], b[k]] for k in a if a[k] != b[k]}}
                output.write(json.dumps(entry) + "\n")
                if len(changes) < 10:
                    changes.append(entry)
            a, b = next(ai, None), next(bi, None)
    return {"unchanged": same, "changed": changed, "removed": removed, "added": added, "examples": changes}


def single_digest(s):
    # Match Java String.length(), a count of UTF-16 code units.
    framed = str(len(s.encode("utf-16-be")) // 2) + ":" + s
    return hashlib.sha256(framed.encode()).hexdigest()


def compare(left, right, output):
    output.mkdir(parents=True, exist_ok=False)
    leaves = compare_rows(left / "leaves.csv", right / "leaves.csv", "instance_key", output / "leaf_differences.jsonl")
    endpoints = compare_rows(left / "endpoints.csv", right / "endpoints.csv", "endpoint", output / "endpoint_differences.jsonl")
    old_summary = json.loads((left / "summary.json").read_text())
    new_summary = json.loads((right / "summary.json").read_text())
    for rows, label in ((leaves, "leaf_instances"), (endpoints, "endpoints")):
        if old_summary[label] != rows["unchanged"] + rows["changed"] + len(rows["removed"]):
            raise ValueError("baseline exported count mismatch")
        if new_summary[label] != rows["unchanged"] + rows["changed"] + len(rows["added"]):
            raise ValueError("candidate exported count mismatch")
    removed = {r["instance_key"]: r for r in leaves["removed"]}
    isolated = []
    empty = hashlib.sha256(b"").hexdigest()
    for pin in endpoints["removed"]:
        leaf = removed.get(pin["instance_key"])
        if leaf is None:
            continue
        expected_pin = {"VCC": "P", "GND": "G"}.get(leaf["type"])
        if (leaf["library"] == "hdi_primitives" and leaf["primitive"] == "true" and expected_pin
                and leaf["port_bits"] == "1" and leaf["properties_sha256"] == empty
                and pin["direction"] == "OUTPUT" and pin["port"] == expected_pin
                and pin["component_terminals"] == "1"
                and pin["component_sha256"] == single_digest(pin["endpoint"])):
            isolated.append(pin["instance_key"])
    strict = not any((leaves["changed"], leaves["removed"], leaves["added"],
                      endpoints["changed"], endpoints["removed"], endpoints["added"]))
    preserved = (not any((leaves["changed"], leaves["added"], endpoints["changed"], endpoints["added"]))
                 and len(isolated) == len(removed) == len(endpoints["removed"])
                 and len(set(isolated)) == len(isolated))
    result = {"schema": "dieroute.edif_connectivity_audit.v1", "left": str(left.resolve()), "right": str(right.resolve()),
              "left_summary": old_summary, "right_summary": new_summary,
              "leaves": leaves, "endpoints": endpoints,
              "strict_exported_terminal_and_leaf_equality": strict,
              "connectivity_preserved_except_isolated_constant_deletion": preserved,
              "isolated_constant_deletions": isolated,
              "scope": "all declared leaf and top-level bits, component membership, leaf instance/type/port properties; primitive and opaque cell boundaries",
              "not_proven": ["encrypted cell internal equivalence", "new routing correctness", "timing model accuracy"],
              "input_hashes": {str(p): sha256(p) for root in (left, right) for p in sorted(root.glob("*.csv"))}}
    (output / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("left", type=Path)
    p.add_argument("right", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    result = compare(args.left, args.right, args.output)
    print(json.dumps({k: result[k] for k in ("strict_exported_terminal_and_leaf_equality", "connectivity_preserved_except_isolated_constant_deletion")}))
    return 0 if result["connectivity_preserved_except_isolated_constant_deletion"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
