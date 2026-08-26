#!/usr/bin/env python3
"""Copy a production-ABI graph and select task records by task ID."""
import argparse
import shutil
import struct
from pathlib import Path

TASK = struct.Struct("<IIIIHHIII")

parser = argparse.ArgumentParser()
parser.add_argument("input_prefix", type=Path)
parser.add_argument("output_prefix", type=Path)
parser.add_argument("task_ids", nargs="+", type=int)
args = parser.parse_args()
wanted = set(args.task_ids)
if len(wanted) != len(args.task_ids):
    raise SystemExit("task IDs must be unique")
raw = args.input_prefix.with_suffix(".tasks").read_bytes()
if len(raw) % TASK.size:
    raise SystemExit("misaligned task input")
selected = []
for offset in range(0, len(raw), TASK.size):
    record = raw[offset : offset + TASK.size]
    if TASK.unpack(record)[0] in wanted:
        selected.append(record)
found = {TASK.unpack(record)[0] for record in selected}
if found != wanted:
    raise SystemExit(f"missing task IDs: {sorted(wanted - found)}")
args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
for suffix in (".nodes", ".edges", ".resources"):
    shutil.copyfile(str(args.input_prefix) + suffix, str(args.output_prefix) + suffix)
Path(str(args.output_prefix) + ".tasks").write_bytes(b"".join(selected))
print(f"selected {len(selected)} tasks: {sorted(found)}")
