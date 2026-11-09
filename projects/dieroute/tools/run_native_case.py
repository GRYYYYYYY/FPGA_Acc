#!/usr/bin/env python3
"""Archive a native multi-die VPR baseline; never overwrite a previous run."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--vpr", type=Path, required=True)
    p.add_argument("--arch", type=Path, required=True)
    p.add_argument("--circuit", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--device", required=True)
    p.add_argument("--channel-width", type=int, default=32)
    p.add_argument("--seed", type=int, default=1)
    args = p.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    sources = {}
    for label in ("vpr", "arch", "circuit"):
        src = getattr(args, label).resolve()
        sources[label] = {"path": str(src), "sha256": sha256(src)}
        if label != "vpr":
            shutil.copyfile(src, output / ("architecture.xml" if label == "arch" else "circuit.blif"))
    cmd = [str(args.vpr.resolve()), "architecture.xml", "circuit.blif",
           "--device", args.device, "--route_chan_width", str(args.channel_width),
           "--seed", str(args.seed), "--num_workers", "1", "--write_rr_graph", "rr_graph.xml"]
    record = {"schema": "dieroute.native_case.v1", "status": "running",
              "sources": sources, "command": cmd, "cwd": str(output),
              "started_unix_ns": time.time_ns(), "evidence_class": "native_vpr_architecture_model",
              "board_result": False}
    manifest = output / "run.json"
    manifest.write_text(json.dumps(record, indent=2) + "\n")
    start = time.monotonic_ns()
    with (output / "vpr.log").open("w") as log:
        process = subprocess.Popen(cmd, cwd=output, stdout=log, stderr=subprocess.STDOUT)
        record["pid"] = process.pid
        manifest.write_text(json.dumps(record, indent=2) + "\n")
        code = process.wait()
    record.update(status="passed" if code == 0 else "failed", returncode=code,
                  elapsed_ns=time.monotonic_ns() - start)
    record["artifacts"] = {f.name: {"bytes": f.stat().st_size, "sha256": sha256(f)}
                           for f in sorted(output.iterdir()) if f.is_file() and f != manifest}
    manifest.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"manifest": str(manifest), "returncode": code}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
