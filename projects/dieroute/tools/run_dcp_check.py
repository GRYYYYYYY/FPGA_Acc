#!/usr/bin/env python3
"""Archive native Vivado reports; report generation alone does not prove legality.

Load the target Vitis/Vivado settings64.sh before invoking this runner.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import time

from run_native_case import sha256


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--export-edif", action="store_true")
    p.add_argument("--load-script", type=Path, help="RapidWright loader for checkpoint plus encrypted EDIF cells")
    args = p.parse_args()
    vivado = shutil.which("vivado")
    if not vivado:
        raise RuntimeError("source the target settings64.sh before running this tool")
    inp, out = args.input.resolve(), args.output.resolve()
    digest = sha256(inp)
    dependencies = {}
    if args.load_script:
        loader = args.load_script.resolve()
        checkpoints = []
        for line in loader.read_text().splitlines():
            if line.startswith("read_edif ") or line.startswith("read_checkpoint "):
                command, name = line.split(maxsplit=1)
                # RapidWright's generated format uses literal absolute paths.
                # Fail closed on quoting/Tcl substitutions rather than guessing.
                dep = Path(name)
                if not dep.is_absolute() or not dep.is_file() or any(c in name for c in "[]{};$\\\"\t "):
                    raise ValueError("unsupported generated loader dependency: " + line)
                dependencies[str(dep)] = sha256(dep)
                if command == "read_checkpoint":
                    checkpoints.append(dep.resolve())
        if checkpoints != [inp]:
            raise ValueError("loader must reference exactly the requested checkpoint")
    out.mkdir(parents=True, exist_ok=False)
    script = Path(__file__).with_name("check_dcp.tcl")
    shutil.copyfile(script, out / script.name)
    shutil.copyfile(__file__, out / Path(__file__).name)
    shutil.copyfile(Path(__file__).with_name("run_native_case.py"), out / "run_native_case.py")
    cmd = [vivado, "-mode", "batch", "-source", str(out / script.name), "-tclargs", str(inp), str(out / "reports")]
    if args.export_edif:
        cmd.append(str(out / "readable.edf"))
    elif args.load_script:
        cmd.append("-")
    if args.load_script:
        shutil.copyfile(loader, out / "checkpoint_load.tcl")
        dependencies[str(loader)] = sha256(loader)
        cmd.append(str(out / "checkpoint_load.tcl"))
    record = {"schema": "dieroute.native_dcp_check.v1", "status": "running", "command": cmd,
              "cwd": str(out), "input": str(inp), "input_sha256": digest,
              "script_sha256": sha256(script), "started_ns": time.time_ns(),
              "board_result": False, "changes_routes": False, "dependencies": dependencies}
    manifest = out / "manifest.json"

    def save():
        tmp = out / "manifest.json.tmp"
        tmp.write_text(json.dumps(record, indent=2) + "\n")
        tmp.replace(manifest)

    save()
    with (out / "console.log").open("w") as log:
        proc = subprocess.Popen(cmd, cwd=out, stdout=log, stderr=subprocess.STDOUT)
        record["pid"] = proc.pid
        save()
        code = proc.wait()
    reports = ["design.txt", "route_status.rpt", "timing_summary.rpt", "utilization.rpt", "drc.rpt", "checks_completed.txt"]
    record["reports_complete"] = all((out / "reports" / f).is_file() for f in reports)
    record["input_unchanged"] = digest == sha256(inp)
    record["dependencies_unchanged"] = all(sha256(Path(name)) == value for name, value in dependencies.items())
    ok = code == 0 and record["reports_complete"] and record["input_unchanged"] and record["dependencies_unchanged"]
    if args.export_edif:
        ok = ok and (out / "readable.edf").is_file()
    record.update(status="reports_generated" if ok else "failed", returncode=code, finished_ns=time.time_ns())
    record["artifacts"] = {str(f.relative_to(out)): sha256(f) for f in sorted(out.rglob("*"))
                           if f.is_file() and f != manifest}
    save()
    print(json.dumps({"manifest": str(manifest), "status": record["status"]}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
