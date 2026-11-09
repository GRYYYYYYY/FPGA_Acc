#!/usr/bin/env python3
"""Freeze and run EDIF connectivity export; no routing or checkpoint changes."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

from run_native_case import sha256


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", action="append", required=True, help="label=/absolute/or/relative/input.edf")
    for name in ("output", "jdk", "cufr", "runtime"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--heap-gb", type=int, default=64)
    p.add_argument("--java-processors", type=int, default=0,
                   help="Optional JVM processor cap; zero preserves JVM default")
    args = p.parse_args()
    if args.heap_gb <= 0 or args.java_processors < 0:
        raise ValueError("invalid JVM resource limits")
    inputs = {}
    for entry in args.input:
        label, path = entry.split("=", 1)
        if not re.fullmatch("[a-z][a-z_0-9]*", label) or label in inputs:
            raise ValueError("invalid or duplicate input label")
        inp = Path(path).resolve()
        inputs[label] = {"input": str(inp), "input_sha256": sha256(inp)}
    if len(inputs) > 3:
        raise ValueError("maximum three simultaneous 64 GiB Java workers")
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out / "classes").mkdir()
    for name in ("EdifConnectivityProbe.java", "run_native_case.py", Path(__file__).name):
        shutil.copyfile(Path(__file__).with_name(name), out / name)
    cufr, jdk = args.cufr.resolve(), args.jdk.resolve()
    cp = str(cufr / "bin") + ":" + str(cufr / "jars/*")
    compile_cmd = [str(jdk / "bin/javac"), "-cp", cp, "-d", str(out / "classes"), str(out / "EdifConnectivityProbe.java")]
    record = {"schema": "dieroute.edif_connectivity_run.v2", "status": "running",
              "cwd": str(out), "runtime": str(args.runtime.resolve()), "started_ns": time.time_ns(),
              "source_sha256": sha256(out / "EdifConnectivityProbe.java"), "compile_command": compile_cmd,
              "runs": inputs, "jars": {str(f): sha256(f) for f in sorted((cufr / "jars").glob("*.jar"))},
              "classpath_classes": {str(f): sha256(f) for f in sorted((cufr / "bin").rglob("*.class"))}}
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
    processes = []
    if rc == 0:
        for label, run in inputs.items():
            cmd = [str(jdk / "bin/java"), "-Xmx" + str(args.heap_gb) + "g"]
            if args.java_processors:
                cmd.append("-XX:ActiveProcessorCount=" + str(args.java_processors))
            cmd += ["-cp", str(out / "classes") + ":" + cp,
                   "EdifConnectivityProbe", run["input"], str(out / label)]
            log = (out / (label + ".log")).open("w")
            proc = subprocess.Popen(cmd, env=env, cwd=out, stdout=log, stderr=subprocess.STDOUT)
            run.update(command=cmd, pid=proc.pid)
            processes.append((run, proc, log))
            save()
        for run, proc, log in processes:
            run["returncode"] = proc.wait()
            log.close()
            save()
    record["inputs_unchanged"] = all(sha256(Path(r["input"])) == r["input_sha256"] for r in inputs.values())
    ok = rc == 0 and all(r.get("returncode") == 0 for r in inputs.values()) and record["inputs_unchanged"]
    record.update(status="passed" if ok else "failed", finished_ns=time.time_ns())
    record["artifacts"] = {str(f.relative_to(out)): sha256(f) for f in sorted(out.rglob("*")) if f.is_file() and f != manifest}
    save()
    print(json.dumps({"manifest": str(manifest), "status": record["status"]}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
