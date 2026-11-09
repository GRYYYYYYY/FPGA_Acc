#!/usr/bin/env python3
"""Native topology verifier: unused resources, null wires and DCP ID remapping."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import struct
import subprocess
from dcp_footprint_test import ABSENT, fixture, mutate, write_table


def graph(out):
    out.mkdir()
    write_table(out / "nodes.bin", [
        [0, 0, 10, 0, 10, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [1, 0, 11, 1, 11, 3, 2, 1, 0, 0, 0, 0, 1, 0, 0, 0],
        [2, 0, 13, 0, 13, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0],
        [3, 0, 14, 0, 14, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [4, 0, 15, 1, 15, 3, 2, 0, 4, 0, 0, 0, 1, 0, 0, 0],
        [5, 1, 12, 1, 12, 2, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0],
    ])
    wires = [[0, 0, 10], [1, 0, 11], [2, 0, 13], [3, 0, 14], [4, 0, 15], [1, 1, 11], [5, 1, 12], [4, 1, 15]]
    write_table(out / "wires.bin", wires)
    valid = {(w[1], w[2]) for w in wires}
    write_table(out / "null_wires.bin", [[t, w] for t in range(2) for w in range(20) if (t, w) not in valid])
    write_table(out / "pips.bin", [[0, ABSENT, 0, 0, 0, 10, 0, 0], [1, 0, 1, 0, 10, 11, 0, 0],
                                   [2, 1, 2, 0, 11, 13, 0, 0], [3, 1, 3, 0, 11, 14, 0, 8],
                                   [4, 3, 1, 0, 14, 11, 0, 2], [5, 5, 1, 1, 12, 11, 1, 0]])
    for name, rows in {
        "tiles.csv": [["address", "name", "type", "slr", "column", "row", "wire_count", "pip_begin", "pip_count"],
                      [0, "T0", "INT", 0, 0, 0, 20, 0, 5], [1, "T1", "INT", 1, 0, 1, 20, 5, 1]],
        "intents.csv": [["id", "name"], [0, "NODE_SINGLE"], [1, "NODE_LAGUNA_DATA"]],
    }.items():
        with (out / name).open("w", newline="") as stream:
            csv.writer(stream).writerows(rows)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--verifier", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    fixture(out / "footprint")
    graph(out / "base")
    cases = [("base", None, None)] + [
        ("wrong_member", ("wires.bin", 3, 6, 0, 4), "node count/ID"),
        ("wrong_mask", ("nodes.bin", 16, 1, 5, 1), "node mask/bbox recount"),
        ("loose_bbox", ("nodes.bin", 16, 1, 11, 9), "node mask/bbox recount"),
        ("wrong_canonical", ("nodes.bin", 16, 1, 1, 1), "canonical representative mismatch"),
        ("wrong_native", ("nodes.bin", 16, 1, 4, 12), "native representative mismatch"),
        ("false_pip_endpoint", ("pips.bin", 8, 3, 2, 2), "PIP endpoint identity"),
        ("null_overlap", ("null_wires.bin", 2, 0, 1, 10), "null/member overlap"),
        ("wrong_tied_flag", ("nodes.bin", 16, 2, 8, 0), "used intent/tied flags differ"),
        ("wrong_pip_kind", ("pips.bin", 8, 5, 7, 8), "DCP PIP absent from native catalog"),
    ]
    results = []
    for name, edit, expected in cases:
        if edit:
            shutil.copytree(out / "base", out / name)
            mutate(out / name / edit[0], *edit[1:])
        cmd = [str(args.verifier.resolve()), str(out / name), str(out / "footprint"), str(out / (name + "_audit"))]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        (out / (name + ".log")).write_text(proc.stdout + proc.stderr)
        if expected:
            assert proc.returncode != 0 and expected in proc.stderr, (name, proc.stderr)
        else:
            assert proc.returncode == 0, proc.stderr
            audit = json.loads((out / "base_audit/audit.json").read_text())
            assert audit["nodes"] == 6 and audit["used_nodes_mapped"] == 4
            assert audit["pips"] == 6 and audit["used_pips_mapped"] == 3
            assert audit["pips_with_missing_node"] == audit["empty_native_member_nodes"] == 1
            assert audit["empty_member_nodes_incident_to_pips"] == audit["used_empty_member_nodes"] == 0
            assert struct.unpack("<4I", (out / "base_audit/footprint_node_map.bin").read_bytes()) == (0, 1, 5, 2)
            assert struct.unpack("<3I", (out / "base_audit/footprint_pip_map.bin").read_bytes()) == (1, 5, 2)
        results.append({"case": name, "passed": True, "returncode": proc.returncode})
    (out / "tests.json").write_text(json.dumps({"passed": True, "cases": results}, indent=2) + "\n")
    print(json.dumps({"passed": True, "cases": len(results)}))


if __name__ == "__main__":
    main()
