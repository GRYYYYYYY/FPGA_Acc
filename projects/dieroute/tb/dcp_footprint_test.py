#!/usr/bin/env python3
"""Hand-constructed graph and corruption tests for the independent verifier."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import struct
import subprocess

ABSENT = 0xffffffff


def write_table(path, records):
    path.write_bytes(b"".join(struct.pack("<" + "I" * len(r), *r) for r in records))


def fixture(out):
    out.mkdir()
    # Net 0 traverses a two-SLR electrical node. Its second PIP is reversed.
    # Net 1 is static background and shares node 1: this is counted, not hidden.
    write_table(out / "nodes.bin", [
        [0, 0, 10, 0, 10, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0],
        [1, 0, 11, 1, 11, 3, 2, 0, 2, 1, 1, 0, 1, 0, 0, 0],
        [2, 1, 12, 1, 12, 2, 1, 0, 1, 0, 1, 4, 0, 0, 0, 0],
        [3, 0, 13, 0, 13, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0],
    ])
    write_table(out / "wires.bin", [[0, 0, 10], [1, 0, 11], [1, 1, 11], [2, 1, 12], [3, 0, 13]])
    write_table(out / "pins.bin", [[0, 0, 0, 1], [0, 2, 1, 0]])
    write_table(out / "pips.bin", [[0, 0, 1, 0, 10, 11, 0, 0], [0, 2, 1, 1, 12, 11, 1, 1], [1, 1, 3, 0, 11, 13, 0, 0]])
    write_table(out / "owners.bin", [[0, 0], [1, 0], [2, 0], [1, 1], [3, 1]])
    write_table(out / "tasks.bin", [[0, 0, 0, 2, 0, 1, 0, 1]])
    write_table(out / "nets.bin", [[0, 0, 0, 0, 2, 0, 2, 0, 1, 0, 3, 1, 1, 0, 0, 0],
                                   [537, ABSENT, ABSENT, 2, 0, 2, 1, 1, 0, 3, 2, 0, 0, 0, 0, 0]])
    for name, rows in {
        "tiles.csv": [["address", "name", "slr", "column", "row", "wire_count"], [0, "T0", 0, 0, 0, 20], [1, "T1", 1, 0, 1, 20]],
        "intents.csv": [["id", "name"], [0, "NODE_SINGLE"], [1, "NODE_LAGUNA_DATA"]],
        "partition_pins.csv": [["node_id", "instance", "terminal", "tile", "wire", "fixed", "wire_fixed", "is_port"], [2, "region", "in", "T1", "W12", "true", "true", "false"]],
    }.items():
        with (out / name).open("w", newline="") as f:
            csv.writer(f).writerows(rows)


def mutate(path, width, row, col, value):
    data = bytearray(path.read_bytes())
    struct.pack_into("<I", data, 4 * (width * row + col), value)
    path.write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verifier", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    fixture(out / "base")
    cases = [("base", None, None)] + [
        ("wrong_membership", ("nodes.bin", 16, 1, 5, 1), "SLR membership mismatch"),
        ("wrong_canonical", ("nodes.bin", 16, 1, 1, 1), "canonical representative mismatch"),
        ("wrong_native", ("nodes.bin", 16, 1, 4, 12), "native representative mismatch"),
        ("lost_partition_marker", ("nodes.bin", 16, 2, 11, 0), "partition marker mismatch"),
        ("wrong_pip_identity", ("pips.bin", 8, 1, 4, 11), "PIP start identity"),
        ("duplicate_owner", ("owners.bin", 2, 2, 0, 1), "duplicate/unsorted net owner"),
        ("hidden_background_owner", ("nodes.bin", 16, 1, 9, 0), "owner recount mismatch"),
        ("wrong_source_pin", ("nets.bin", 16, 0, 2, 1), "source pin mismatch"),
        ("wrong_task_pin", ("tasks.bin", 8, 0, 7, 0), "task pin identity"),
        ("wrong_access_slr", ("pins.bin", 4, 1, 2, 0), "pin access outside node membership"),
        ("wrong_task_coverage", ("nets.bin", 16, 0, 8, 0), "candidate task coverage"),
        ("wrong_exclusion", ("nets.bin", 16, 1, 0, 1), "candidate exclusion reason inconsistent"),
        ("reverse_direction", ("pips.bin", 8, 1, 7, 0), None),
    ]
    results = []
    for name, edit, error in cases:
        if edit:
            shutil.copytree(out / "base", out / name)
            mutate(out / name / edit[0], *edit[1:])
        cmd = [str(args.verifier.resolve()), str(out / name), str(out / (name + "_audit"))]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        (out / (name + ".log")).write_text(proc.stdout + proc.stderr)
        if error:
            assert proc.returncode != 0 and error in proc.stderr, (name, proc.returncode, proc.stderr)
        else:
            assert proc.returncode == 0, (name, proc.stderr)
            audit = json.loads((out / (name + "_audit") / "audit.json").read_text())
            assert audit["unreachable_candidate_sinks"] == (1 if name == "reverse_direction" else 0)
            assert audit["multi_owner_nodes"] == audit["shared_candidate_background_nodes"] == 1
            assert audit["owned_cross_slr_laguna_nodes"] == 1
            assert audit["candidate_nets_touching_partition_pins"] == 1
            assert audit["partition_pins"] == audit["protected_partition_nodes"] == 1
            assert audit["candidate_owned_sll_nodes"] == audit["background_owned_sll_nodes"] == 1
            assert audit["cross_slr_candidate_tasks"] == 1
        results.append({"case": name, "passed": True, "returncode": proc.returncode})
    (out / "tests.json").write_text(json.dumps({"passed": True, "cases": results}, indent=2) + "\n")
    print(json.dumps({"passed": True, "cases": len(results)}))


if __name__ == "__main__":
    main()
