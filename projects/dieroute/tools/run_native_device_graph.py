#!/usr/bin/env python3
"""Freeze and enumerate the complete native device topology without routing."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from run_native_case import sha256


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--device", required=True)
    for name in ("output", "jdk", "cufr", "runtime"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out / "classes").mkdir()
    for name in ("NativeDeviceGraph.java", "run_native_case.py", Path(__file__).name):
        shutil.copyfile(Path(__file__).with_name(name), out / name)
    cufr, jdk = args.cufr.resolve(), args.jdk.resolve()
    cp = str(cufr / "bin") + ":" + str(cufr / "jars/*")
    compile_cmd = [str(jdk / "bin/javac"), "-cp", cp, "-d", str(out / "classes"), str(out / "NativeDeviceGraph.java")]
    cmd = [str(jdk / "bin/java"), "-Xmx128g", "-cp", str(out / "classes") + ":" + cp,
           "NativeDeviceGraph", args.device, str(out / "graph")]
    record = {"schema": "dieroute.native_device_graph_run.v1", "status": "running", "device": args.device,
              "cwd": str(out), "runtime": str(args.runtime.resolve()), "started_ns": time.time_ns(),
              "compile_command": compile_cmd, "command": cmd,
              "runtime_data": {str(f): sha256(f) for f in sorted(args.runtime.resolve().rglob("*.dat"))},
              "jars": {str(f): sha256(f) for f in sorted((cufr / "jars").glob("*.jar"))},
              "classpath_classes": {str(f): sha256(f) for f in sorted((cufr / "bin").rglob("*.class"))},
              "source_sha256": {f.name: sha256(f) for f in out.iterdir() if f.is_file()}}
    manifest = out / "manifest.json"

    def save():
        temp = out / "manifest.tmp"
        temp.write_text(json.dumps(record, indent=2) + "\n")
        temp.replace(manifest)

    env = dict(os.environ, RAPIDWRIGHT_PATH=str(args.runtime.resolve()))
    save()
    with (out / "compile.log").open("w") as log:
        rc = subprocess.run(compile_cmd, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
    record["compile_returncode"] = rc
    if rc == 0:
        with (out / "export.log").open("w") as log:
            proc = subprocess.Popen(cmd, env=env, cwd=out, stdout=log, stderr=subprocess.STDOUT)
            record["pid"] = proc.pid
            save()
            record["returncode"] = proc.wait()
    record["dependencies_unchanged"] = all(sha256(Path(f)) == h for group in ("runtime_data", "jars", "classpath_classes") for f, h in record[group].items())
    ok = rc == 0 and record.get("returncode") == 0 and record["dependencies_unchanged"]
    record.update(status="passed" if ok else "failed", finished_ns=time.time_ns())
    record["artifacts"] = {str(f.relative_to(out)): sha256(f) for f in sorted(out.rglob("*")) if f.is_file() and f != manifest}
    save()
    print(json.dumps({"manifest": str(manifest), "status": record["status"]}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
