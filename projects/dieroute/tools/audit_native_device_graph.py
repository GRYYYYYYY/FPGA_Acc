#!/usr/bin/env python3
"""Verify complete raw native topology and map the complete original DCP into it."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import time
from run_native_case import sha256


def main():
    if not __debug__:
        raise RuntimeError("run without optimization; audit assertions are mandatory")
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("graph", "footprint", "verifier", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    for name in (Path(__file__).name, "run_native_case.py", "verify_native_device_graph.cpp"):
        shutil.copyfile(Path(__file__).with_name(name), out / name)
    graph, footprint = args.graph.resolve(), args.footprint.resolve()
    gm = json.loads((graph / "manifest.json").read_text())
    fm = json.loads((footprint / "manifest.json").read_text())
    assert gm["schema"] == "dieroute.native_device_graph_run.v1" and gm["dependencies_unchanged"]
    assert fm["schema"] == "dieroute.dcp_footprint_run.v1" and fm["inputs_unchanged"]
    assert gm["status"] == fm["status"] == "passed"
    assert gm["compile_returncode"] == gm["returncode"] == fm["compile_returncode"] == fm["returncode"] == 0
    assert gm["runtime"] == fm["runtime"]
    assert gm["jars"] == fm["jars"] and gm["classpath_classes"] == fm["classpath_classes"]
    manifest = out / "manifest.json"
    record = {"schema": "dieroute.native_device_graph_cross_audit.v1", "status": "running", "started_ns": time.time_ns(),
              "graph_manifest": str(graph / "manifest.json"), "graph_manifest_sha256": sha256(graph / "manifest.json"),
              "footprint_manifest": str(footprint / "manifest.json"), "footprint_manifest_sha256": sha256(footprint / "manifest.json"),
              "verifier_sha256": sha256(args.verifier)}

    def save():
        temp = out / "manifest.tmp"
        temp.write_text(json.dumps(record, indent=2) + "\n")
        temp.replace(manifest)

    save()
    try:
        for label, producer, m in (("graph", graph, gm), ("footprint", footprint, fm)):
            for f, h in m["artifacts"].items():
                assert sha256(producer / f) == h, str(producer / f)
            record[label + "_artifacts_verified"] = len(m["artifacts"])
            save()
        for group in ("runtime_data", "jars", "classpath_classes"):
            for path, h in gm[group].items():
                assert sha256(Path(path)) == h, path
        for path, h in fm["inputs"].items():
            assert sha256(Path(path)) == h, path
        cmd = [str(args.verifier.resolve()), str(graph / "graph"), str(footprint / "footprint"), str(out / "binary_audit")]
        record["command"] = cmd
        with (out / "verify.log").open("w") as log:
            proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            record["pid"] = proc.pid
            save()
            record["returncode"] = proc.wait()
        assert record["returncode"] == 0, "binary verifier failed"
        audit = json.loads((out / "binary_audit/audit.json").read_text())
        summary = json.loads((graph / "graph/summary.json").read_text())
        assert summary["schema"] == "dieroute.native_device_graph.v2"
        for name in summary.keys() & audit.keys() - {"schema", "scope"}:
            assert summary[name] == audit[name], name
        fs = json.loads((footprint / "footprint/summary.json").read_text())
        assert audit["used_nodes_mapped"] == fs["nodes"]
        assert audit["used_member_wires_mapped"] == fs["member_wires"]
        assert audit["used_pips_mapped"] == fs["pips"]
        assert audit["used_sll_nodes"] == fs["owned_cross_slr_laguna_nodes"]
        assert sha256(args.verifier) == record["verifier_sha256"]
        record.update(status="passed", scope="exhaustive raw topology and original DCP mappings; no design eligibility, capacity/delay or rerouting claim")
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
