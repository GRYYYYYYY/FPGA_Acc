#!/usr/bin/env python3
"""Locate hierarchy/instance-property differences; not logical equivalence."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path

from run_native_case import sha256


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    root, out = args.input, args.output
    m = json.loads((root / "manifest.json").read_text())
    if m["status"] != "passed" or any(r["returncode"] for r in m["runs"].values()):
        raise ValueError("hierarchy extraction incomplete")
    for name, digest in m["artifacts"].items():
        if sha256(root / name) != digest:
            raise ValueError("hierarchy extraction artifact changed")
    for run in m["runs"].values():
        if sha256(Path(run["input"])) != run["input_sha256"]:
            raise ValueError("hierarchy extraction input changed")
    out.mkdir(parents=True, exist_ok=False)
    base, mid, final = [root / (s + ".csv") for s in ("baseline", "rw_embedded", "native_roundtrip")]
    removed, added, examples = [], [], []
    fields = Counter()
    changed = equal = 0
    with base.open() as a, final.open() as b, (out / "changed_rows.jsonl").open("w") as output:
        ai, bi = iter(csv.DictReader(a)), iter(csv.DictReader(b))
        x, y = next(ai, None), next(bi, None)
        while x is not None or y is not None:
            if y is None or (x is not None and x["instance"] < y["instance"]):
                removed.append(x)
                x = next(ai, None)
                continue
            if x is None or y["instance"] < x["instance"]:
                added.append(y)
                y = next(bi, None)
                continue
            if x == y:
                equal += 1
            else:
                changed += 1
                diff = {k: [x[k], y[k]] for k in x if x[k] != y[k]}
                fields.update(diff.keys())
                row = {"instance": x["instance"], "differences": diff}
                output.write(json.dumps(row) + "\n")
                if len(examples) < 10:
                    examples.append(row)
            x, y = next(ai, None), next(bi, None)
    hashes = {p.name: sha256(p) for p in (base, mid, final)}
    result = {"schema": "dieroute.edif_hierarchy_audit.v1", "input": str(root.resolve()),
              "producer_manifest_sha256": sha256(root / "manifest.json"), "inputs": hashes,
              "baseline_vs_rw_embedded_byte_equal": hashes[base.name] == hashes[mid.name],
              "baseline_vs_native_roundtrip": {"removed": removed, "added": added,
                  "changed_rows": changed, "unchanged_rows": equal, "changed_fields": dict(fields), "examples": examples},
              "scope": "hierarchy and instance properties only; encrypted cells are not elaborated; not full logical equivalence"}
    (out / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
