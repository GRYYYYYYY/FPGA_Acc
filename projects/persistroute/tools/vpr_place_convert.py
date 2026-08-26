#!/usr/bin/env python3
"""Convert a VPR .place text file into deterministic CSV plus metadata."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


def parse(path: Path):
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        text = line.strip()
        if not text or text.startswith("#") or text.startswith("Netlist_File:") or text.startswith("Array size:"):
            continue
        fields = re.split(r"\s+", text)
        if len(fields) < 4:
            continue
        try:
            x, y, subtile = int(fields[1]), int(fields[2]), int(fields[3])
        except ValueError:
            continue
        rows.append({"block": fields[0], "x": x, "y": y, "subtile": subtile, "line": line_number})
    if len({row["block"] for row in rows}) != len(rows):
        raise ValueError("duplicate block in placement")
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = parse(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["block", "x", "y", "subtile", "line"])
        writer.writeheader()
        writer.writerows(rows)
    metadata = {
        "source": str(args.input.resolve()),
        "source_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "rows": len(rows),
        "output_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
    }
    args.output.with_suffix(args.output.suffix + ".json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
