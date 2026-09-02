#!/usr/bin/env python3
"""Validate and summarize the frozen external VPR constraint cases."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from tileplace_vpr import ContractError, dump_json, sha256


CASES = (
    "bigkey_tight_seed3_cw300_v2",
    "apex4_fixed_io_seed1_cw78_v2",
)


def load(path: Path) -> dict:
    if not path.is_file():
        raise ContractError(f"missing evidence file: {path}")
    return json.loads(path.read_text())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments", type=Path, default=Path(__file__).parents[1] / "experiments")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--ap-failure-log",
        type=Path,
        default=Path(__file__).parents[1]
        / "work/apex4_fixed_io_seed1_cw78/baseline.stdout.log",
    )
    parser.add_argument(
        "--ap-failure-stderr",
        type=Path,
        default=Path(__file__).parents[1]
        / "work/apex4_fixed_io_seed1_cw78/baseline.stderr.log",
    )
    args = parser.parse_args()
    try:
        experiments = args.experiments.resolve()
        rows = []
        for directory_name in CASES:
            directory = experiments / directory_name
            case = load(directory / "external_constraint_case.json")
            manifest = load(directory / "manifest.json")
            probe = load(directory / "constraint_recovery_probe.json")
            baseline_closure = load(directory / "vpr_native_closure.json")
            recovered_closure = load(directory / "recovered_vpr_native_closure.json")
            for evidence in (case, probe, baseline_closure, recovered_closure):
                if evidence.get("status") != "pass":
                    raise ContractError(f"{directory_name}: non-passing evidence")
            if not baseline_closure.get("legal") or not recovered_closure.get("legal"):
                raise ContractError(f"{directory_name}: native closure is not legal")
            source = directory / "source.vpr_constraints.xml"
            if sha256(source) != case["source"]["sha256"]:
                raise ContractError(f"{directory_name}: source constraint hash mismatch")
            if manifest["inputs"]["vpr_constraints"]["sha256"] != sha256(source):
                raise ContractError(f"{directory_name}: manifest constraint hash mismatch")
            for closure in (baseline_closure, recovered_closure):
                command = closure["command"]
                if "--read_vpr_constraints" not in command:
                    raise ContractError(f"{directory_name}: native closure omitted VPR constraints")
                constraint_index = command.index("--read_vpr_constraints") + 1
                if sha256(Path(command[constraint_index])) != sha256(source):
                    raise ContractError(f"{directory_name}: closure used a different constraint file")
            if baseline_closure["wirelength"] != case["baseline"]["wirelength"]:
                raise ContractError(f"{directory_name}: baseline wirelength mismatch")
            if baseline_closure["cpd_ns"] != case["baseline"]["cpd_ns"]:
                raise ContractError(f"{directory_name}: baseline CPD mismatch")
            if recovered_closure["inputs"]["golden_place"]["sha256"] != probe["recovered_place"]["sha256"]:
                raise ContractError(f"{directory_name}: recovered closure placement mismatch")
            if probe["repeat_sha256"] != probe["recovered_place"]["sha256"]:
                raise ContractError(f"{directory_name}: recovery repeat mismatch")
            rows.append(
                {
                    "case": case["case"],
                    "directory": directory_name,
                    "source": case["source"],
                    "seed": manifest["vpr"]["seed"],
                    "channel_width": manifest["vpr"]["channel_width"],
                    "blocks": case["contract"]["blocks"],
                    "sites": case["contract"]["sites"],
                    "nets": case["contract"]["nets"],
                    "constraints": case["constraints"],
                    "reference": {
                        "deterministic": case["cpu_golden"]["deterministic_repeat"],
                        "moved_blocks": case["cpu_golden"]["moved_blocks"],
                        "native_routing_iterations": baseline_closure["routing_iterations"],
                        "native_wirelength": baseline_closure["wirelength"],
                        "native_cpd_ns": baseline_closure["cpd_ns"],
                    },
                    "violation_probe": {
                        "injection": probe["injection"],
                        "validator_rejection": probe["validator_rejection"],
                        "moved_from_input": probe["recovery"]["moved_from_input"],
                        "deterministic_recovery_sha256": probe["recovered_place"]["sha256"],
                        "native_routing_iterations": recovered_closure["routing_iterations"],
                        "native_wirelength": recovered_closure["wirelength"],
                        "native_cpd_ns": recovered_closure["cpd_ns"],
                    },
                }
            )

        ap_log = args.ap_failure_log.resolve()
        ap_stderr = args.ap_failure_stderr.resolve()
        ap_text = ap_log.read_text() + ap_stderr.read_text()
        fixed_match = re.search(r"Fixed Blocks:\s+(\d+)", ap_text)
        dependency_marker = "QP Hybrid Solver requires the Eigen library"
        if not fixed_match or dependency_marker not in ap_text:
            raise ContractError("analytical-placement failure log lacks expected evidence")
        summary = {
            "schema": "TILEPLACE_EXTERNAL_CONSTRAINT_MATRIX_V1",
            "status": "pass",
            "date": "2026-08-31",
            "vtr_revision": "8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07",
            "cases": rows,
            "totals": {
                "cases": len(rows),
                "blocks": sum(row["blocks"] for row in rows),
                "constrained_clusters": sum(row["constraints"]["constrained_clusters"] for row in rows),
                "coordinate_fixed_clusters": sum(
                    row["constraints"]["coordinate_fixed_clusters"] for row in rows
                ),
                "matched_atoms": sum(row["constraints"]["matched_atoms"] for row in rows),
            },
            "analytical_place_attempt": {
                "status": "environment_dependency_missing",
                "recognized_fixed_blocks": int(fixed_match.group(1)),
                "error": dependency_marker,
                "log_path": str(ap_log),
                "log_sha256": sha256(ap_log),
                "stderr_path": str(ap_stderr),
                "stderr_sha256": sha256(ap_stderr),
                "interpretation": (
                    "The official AP mode recognized the fixed constraints but this VPR build lacks Eigen; "
                    "the passing fixed-I/O case therefore uses conventional VPR placement with the same XML."
                ),
            },
            "claim_boundary": (
                "These cases prove external VPR constraint import, deterministic CPU legality recovery, "
                "and VPR-native route/analysis closure. Reference and recovery QoR values are not "
                "TilePlace placement improvements or hardware performance results."
            ),
        }
        dump_json(args.output.resolve(), summary)
        print(json.dumps({"status": "pass", **summary["totals"]}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"prepare_external_constraint_matrix: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
