#!/usr/bin/env python3
"""Check hand-specified groups and adverse mutations of native EDIF fixtures."""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from audit_edif_connectivity import compare


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("fixtures", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.fixtures / "base/leaves.csv").open() as f:
        names = {r["instance_key"]: r["instance"] for r in csv.DictReader(f)}
    groups = defaultdict(set)
    with (args.fixtures / "base/endpoints.csv").open() as f:
        for r in csv.DictReader(f):
            label = names[r["instance_key"]] if r["instance_key"] else "TOP"
            groups[r["component_sha256"]].add(label + "/" + r["port"])
    expected = [
        {"TOP/T[3]", "u0/w/gate/A[2]"}, {"TOP/T[2]", "u0/w/gate/A[3]"},
        {"TOP/T[1]", "u1/w/gate/A[2]"}, {"TOP/T[0]", "u1/w/gate/A[3]"},
        {"TOP/O[1]", "u0/w/gate/Y"}, {"TOP/O[0]", "u1/w/gate/Y"},
        {"TOP/BIO", "u0/w/gate/IO", "u1/w/gate/IO"},
        {"used_const/P", "u0/w/gate/U"}, {"u1/w/gate/U"},
        {"u0/w/gate/SPARE"}, {"u1/w/gate/SPARE"}, {"dead_const/P"},
    ]
    assert set(map(frozenset, groups.values())) == set(map(frozenset, expected)), groups
    results = {"explicit_21_endpoint_12_component_oracle": "passed"}
    for name, accepted in (("rename", True), ("drop_dead", True), ("swap", False),
                           ("drop_used", False), ("property", False), ("drop_spare", False)):
        result = compare(args.fixtures / "base", args.fixtures / name, args.output / name)
        actual = result["connectivity_preserved_except_isolated_constant_deletion"]
        assert actual == accepted, (name, actual, accepted)
        if name == "rename":
            assert result["strict_exported_terminal_and_leaf_equality"]
        if name == "drop_dead":
            assert len(result["isolated_constant_deletions"]) == 1
        results[name] = {"expected_acceptance": accepted, "actual_acceptance": actual, "test": "passed"}
    (args.output / "tests.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
