#!/usr/bin/env python3
"""Build and independently verify a full directed native CSR with provenance."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
from run_native_case import sha256


def main():
    if not __debug__:
        raise RuntimeError("audit assertions require Python without optimization")
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("graph", "mapping_audit", "footprint", "builder", "verifier", "output"):
        p.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    for name in (Path(__file__).name, "run_native_case.py", "build_native_csr.cpp", "verify_native_csr.cpp"):
        shutil.copyfile(Path(__file__).with_name(name), out / name)
    shutil.copyfile(Path(__file__).parent.parent / "include/native_csr_io.hpp", out / "native_csr_io.hpp")
    graph, mapping, footprint = args.graph.resolve(), args.mapping_audit.resolve(), args.footprint.resolve()
    gm = json.loads((graph / "manifest.json").read_text())
    mm = json.loads((mapping / "manifest.json").read_text())
    fm = json.loads((footprint / "manifest.json").read_text())
    assert gm["status"] == mm["status"] == fm["status"] == "passed"
    assert mm["graph_manifest_sha256"] == sha256(graph / "manifest.json")
    assert mm["footprint_manifest_sha256"] == sha256(footprint / "manifest.json")
    assert json.loads((graph / "graph/summary.json").read_text())["schema"] == "dieroute.native_device_graph.v2"
    inputs = {}
    for name in ("nodes.bin", "pips.bin"):
        inputs[str(graph / "graph" / name)] = gm["artifacts"]["graph/" + name]
    for name in ("occupied_nodes.bin", "footprint_node_map.bin", "footprint_pip_map.bin"):
        inputs[str(mapping / "binary_audit" / name)] = mm["artifacts"]["binary_audit/" + name]
    inputs[str(footprint / "footprint/pips.bin")] = fm["artifacts"]["footprint/pips.bin"]
    descriptor = {"schema": "dieroute.native_device_graph.v2", "nodes_sha256": gm["artifacts"]["graph/nodes.bin"], "pips_sha256": gm["artifacts"]["graph/pips.bin"]}
    architecture_hash = hashlib.sha256(json.dumps(descriptor, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    arch = architecture_hash[:32]
    record = {"schema": "dieroute.native_csr_run.v1", "status": "running", "started_ns": time.time_ns(),
              "inputs": inputs, "source_descriptor": descriptor, "architecture_sha256": architecture_hash,
              "parent_manifests": {str(d / "manifest.json"): sha256(d / "manifest.json") for d in (graph, mapping, footprint)},
              "executables": {str(f.resolve()): sha256(f) for f in (args.builder, args.verifier)}, "steps": []}
    manifest = out / "manifest.json"

    def save():
        temp = out / "manifest.tmp"
        temp.write_text(json.dumps(record, indent=2) + "\n")
        temp.replace(manifest)

    save()
    try:
        for f, h in inputs.items():
            assert sha256(Path(f)) == h, f
        commands = [
            ("build", [str(args.builder.resolve()), str(graph / "graph"), str(mapping / "binary_audit"), arch, str(out / "csr")]),
            ("verify", [str(args.verifier.resolve()), str(graph / "graph"), str(mapping / "binary_audit"), str(footprint / "footprint"), str(out / "csr"), arch, str(out / "audit")]),
        ]
        for label, cmd in commands:
            step = {"name": label, "command": cmd, "started_ns": time.time_ns()}
            record["steps"].append(step)
            with (out / (label + ".log")).open("w") as log:
                proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
                step["pid"] = proc.pid
                save()
                step["returncode"] = proc.wait()
            step["finished_ns"] = time.time_ns()
            save()
            assert step["returncode"] == 0, label + " failed"
        built = json.loads((out / "csr/summary.json").read_text())
        audited = json.loads((out / "audit/audit.json").read_text())
        for name in built.keys() & audited.keys() - {"schema", "scope"}:
            assert built[name] == audited[name], name
        for group in ("inputs", "parent_manifests", "executables"):
            for f, h in record[group].items():
                assert sha256(Path(f)) == h, f
        record.update(status="passed", inputs_unchanged=True)
    except Exception as exc:
        record.update(status="failed", error=repr(exc))
        raise
    finally:
        record["finished_ns"] = time.time_ns()
        record["artifacts"] = {str(f.relative_to(out)): sha256(f) for f in sorted(out.rglob("*")) if f.is_file() and f != manifest}
        save()
    print(json.dumps({"manifest": str(manifest), "status": record["status"]}))


if __name__ == "__main__":
    main()
