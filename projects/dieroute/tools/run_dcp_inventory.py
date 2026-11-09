#!/usr/bin/env python3
"""Freeze and run native DCP inventory, optionally serialize an unchanged DCP.

Requires an explicit readable EDIF from Vivado. Success is not native legality
or DieRoute rerouting evidence; run check_dcp.tcl on both checkpoints separately.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from run_native_case import sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("input", "edif", "output", "jdk", "cufr", "runtime"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--roundtrip", action="store_true")
    args = parser.parse_args()
    inputs = {name: getattr(args, name).resolve() for name in ("input", "edif")}
    if any(not p.is_file() for p in inputs.values()):
        raise ValueError("both checkpoint and explicit readable EDIF must exist")
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).with_name("DcpSlrProbe.java")
    shutil.copyfile(source, out / source.name)
    shutil.copyfile(__file__, out / Path(__file__).name)
    shutil.copyfile(Path(__file__).with_name("run_native_case.py"), out / "run_native_case.py")
    (out / "classes").mkdir()
    cufr, jdk = args.cufr.resolve(), args.jdk.resolve()
    cp = str(cufr / "bin") + ":" + str(cufr / "jars/*")
    compile_cmd = [str(jdk / "bin/javac"), "-cp", cp, "-d", str(out / "classes"), str(out / source.name)]
    run_cmd = [str(jdk / "bin/java"), "-Xmx64g", "-cp", str(out / "classes") + ":" + cp,
               "DcpSlrProbe", str(inputs["input"]), str(out / "inventory"), str(inputs["edif"])]
    if args.roundtrip:
        run_cmd.append(str(out / "roundtrip.dcp"))
    record = {"schema": "dieroute.dcp_inventory.v3", "status": "running",
              "scope": "inventory_and_optional_unmodified_serialization",
              "inputs": {k: {"path": str(p), "sha256": sha256(p)} for k, p in inputs.items()},
              "source_sha256": sha256(source), "runtime": str(args.runtime.resolve()),
              "commands": [compile_cmd, run_cmd], "cwd": str(out), "started_ns": time.time_ns(),
              "board_result": False, "routes_recomputed": False, "steps": [],
              "jars": {str(p): sha256(p) for p in sorted((cufr / "jars").glob("*.jar"))},
              "runtime_data": {str(p): sha256(p) for p in sorted(args.runtime.resolve().rglob("*.dat"))},
              "classpath_classes": {str(p): sha256(p) for p in sorted((cufr / "bin").rglob("*.class"))}}
    manifest = out / "manifest.json"

    def save():
        tmp = out / "manifest.json.tmp"
        tmp.write_text(json.dumps(record, indent=2) + "\n")
        tmp.replace(manifest)

    env = dict(os.environ, RAPIDWRIGHT_PATH=str(args.runtime.resolve()), RW_AUTO_GENERATE_READABLE_EDIF="0")
    save()
    for name, cmd in zip(("compile", "inventory"), (compile_cmd, run_cmd)):
        with (out / (name + ".log")).open("w") as log:
            process = subprocess.Popen(cmd, cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT)
            record.update(active_step=name, pid=process.pid)
            save()
            code = process.wait()
        record["steps"].append({"name": name, "returncode": code})
        if code:
            break
    record.update(status="passed" if code == 0 else "failed", returncode=code,
                  active_step=None, finished_ns=time.time_ns())
    record["artifacts"] = {str(p.relative_to(out)): sha256(p) for p in sorted(out.rglob("*"))
                           if p.is_file() and p != manifest}
    record["inputs_unchanged"] = all(sha256(inputs[k]) == v["sha256"] for k, v in record["inputs"].items())
    if not record["inputs_unchanged"]:
        record["status"] = "input_changed"
        code = 1
    save()
    print(json.dumps({"manifest": str(manifest), "status": record["status"]}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
