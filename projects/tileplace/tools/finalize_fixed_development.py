#!/usr/bin/env python3
"""Wait for the original controller, audit its terminal result, then build the paper."""

import argparse
import json
import re
import subprocess
import time
from pathlib import Path

from tileplace_vpr import ContractError, dump_json, sha256


def process_start(pid):
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        return None if fields[0] == "Z" else fields[19]
    except FileNotFoundError:
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controller-pid", type=int, required=True)
    parser.add_argument("--controller-start", required=True)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments/tileplace_fixed_development_2026-09-29"
    receipt = root / "finalization.json"
    lock = root / "finalization.lock"
    # One finalizer; this process never submits or restarts a solver.
    with lock.open("x") as stream:
        stream.write(f"controller {args.controller_pid} start {args.controller_start}\n")
    dump_json(receipt, {"status": "waiting_for_original_controller", "controller_pid": args.controller_pid,
                       "controller_start": args.controller_start})
    while process_start(args.controller_pid) == args.controller_start:
        time.sleep(10)
    summary = root / "summary.json"
    if not summary.exists():
        raise ContractError("controller ended without complete summary; no retries")
    audit = project / "experiments/tileplace_fixed_development_audit_2026-09-29.json"
    commands = [
        ["python3", str(project / "tools/audit_fixed_development.py"), "--output", str(audit)],
        ["python3", str(project / "paper/prepare_artifacts.py")],
        ["bash", "-c", 'source "$1" && make -C "$2"', "tileplace-paper",
         "/inspire/hdd/global_user/guoruiyuan-253208540291/texlive/setup.sh", str(project / "paper/dac")],
    ]
    for index, command in enumerate(commands):
        dump_json(receipt, {"status": "finalizing", "step": index, "command": command})
        with (root / f"finalization_{index}.log").open("w") as output:
            process = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, check=False)
        if process.returncode:
            raise ContractError(f"finalization step {index} failed; see retained log")
    paper = project / "paper/dac"
    log = (paper / "main.log").read_text()
    if re.search(r"^!|Overfull|undefined control sequence|Citation .* undefined|Reference .* undefined", log, re.MULTILINE | re.IGNORECASE):
        raise ContractError("paper log contains unresolved error/reference/overfull box")
    match = re.search(r"Output written on main.pdf \((\d+) pages, (\d+) bytes\)", log)
    if not match:
        raise ContractError("paper log missing final PDF output receipt")
    result = {"schema": "TILEPLACE_FIXED_DEVELOPMENT_FINALIZATION_V1", "status": "pass",
              "summary_sha256": sha256(summary), "audit_sha256": sha256(audit),
              "pdf": {"path": str(paper / "main.pdf"), "sha256": sha256(paper / "main.pdf"),
                      "pages": int(match[1]), "bytes": int(match[2])},
              "log_sha256": sha256(paper / "main.log"),
              "scope": "Fixed observed-development validation and paper build; does not close historical held-out provenance"}
    dump_json(receipt, result)
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    try:
        main()
    except ContractError as error:
        root = Path(__file__).resolve().parents[1] / "experiments/tileplace_fixed_development_2026-09-29"
        dump_json(root / "finalization.json", {"status": "fail", "error": str(error), "automatic_retry": False})
        raise
