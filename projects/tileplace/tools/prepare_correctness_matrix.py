#!/usr/bin/env python3
"""Validate and summarize the frozen TilePlace real-case correctness matrix."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path


CASES = (
    ("diffeq", "diffeq_seed1_cw200", "diffeq_seed1_cw200"),
    ("frisc", "frisc_seed1_cw200", "frisc_seed1_cw200"),
    ("elliptic", "elliptic_seed1_cw200", "elliptic_seed1_cw200"),
    ("clma", "clma_seed1_cw200", "clma_seed1_cw200"),
    ("koios_conv_layer", "koios_conv_layer_seed1_cw300", "koios_conv_layer_seed1_cw300"),
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def jsonl(path: Path):
    with path.open() as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).parents[3])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    experiments = repo / "projects" / "tileplace" / "experiments"
    baselines = repo / "projects" / "persistroute" / "experiments" / "vpr9" / "baseline_runs" / "vpr_serial"

    rows = []
    try:
        for case, contract_name, baseline_name in CASES:
            contract = experiments / contract_name
            baseline = baselines / baseline_name
            manifest = read_json(contract / "manifest.json")
            golden = read_json(contract / "golden_validation.json")
            native = read_json(contract / "vpr_native_closure.json")
            macro_capture = read_json(contract / "vpr_macro_capture.json")
            metrics = read_json(baseline / "metrics.json")
            baseline_run = read_json(baseline / "run.json")

            if manifest["schema"] != "TILEPLACE_VPR_CONTRACT_V1":
                raise ValueError(f"{case}: bad contract schema")
            if not golden.get("legal") or golden.get("moved_blocks") != 0:
                raise ValueError(f"{case}: CPU golden is not a zero-move legal reference")
            if native.get("status") != "pass" or not native.get("legal"):
                raise ValueError(f"{case}: native VPR closure did not pass")
            if macro_capture.get("status") != "pass":
                raise ValueError(f"{case}: VPR macro capture did not pass")
            macro_hash = manifest["inputs"]["native_macros"]["sha256"]
            if macro_capture["output"]["sha256"] != macro_hash:
                raise ValueError(f"{case}: captured macro hash differs from contract")
            if native["outputs"]["native_macros"]["sha256"] != macro_hash:
                raise ValueError(f"{case}: closure-regenerated macro hash differs from contract")
            if native["wirelength"] != int(metrics["vpr_wirelength"]):
                raise ValueError(f"{case}: native wirelength differs from frozen baseline")
            if not math.isclose(native["cpd_ns"], metrics["vpr_cpd_ns"], rel_tol=0.0, abs_tol=1e-12):
                raise ValueError(f"{case}: native CPD differs from frozen baseline")
            if not metrics.get("vpr_routed"):
                raise ValueError(f"{case}: frozen baseline was not routed")
            if native["inputs"]["architecture"]["sha256"] != baseline_run["inputs"][0]["sha256"]:
                raise ValueError(f"{case}: architecture hash differs from baseline")
            if native["inputs"]["circuit"]["sha256"] != baseline_run["inputs"][1]["sha256"]:
                raise ValueError(f"{case}: circuit hash differs from baseline")

            block_types = Counter()
            native_macro_ids = set()
            native_macro_members = 0
            for block in jsonl(contract / "blocks.jsonl"):
                block_types[block["logical_type"]] += 1
                if (block.get("macro") or {}).get("source") == "vpr_direct":
                    native_macro_ids.add(block["macro"]["id"])
                    native_macro_members += 1
            if len(native_macro_ids) != manifest["placement_macros"]["macro_count"]:
                raise ValueError(f"{case}: packed native macro count is inconsistent")
            if native_macro_members != manifest["placement_macros"]["member_count"]:
                raise ValueError(f"{case}: packed native macro member count is inconsistent")
            site_types = Counter()
            for site in jsonl(contract / "sites.jsonl"):
                site_types[site["physical_type"]] += 1
            connections = 0
            timed_connections = 0
            pins = 0
            for net in jsonl(contract / "nets.jsonl"):
                pins += len(net["pins"])
                connections += len(net["connections"])
                timed_connections += sum("criticality_q" in connection for connection in net["connections"])

            heterogeneous_blocks = sum(
                count for kind, count in block_types.items() if kind.lower() not in {"clb", "io", "lab"}
            )
            row = {
                    "case": case,
                    "contract": contract_name,
                    "blocks": sum(block_types.values()),
                    "block_types": dict(sorted(block_types.items())),
                    "sites": sum(site_types.values()),
                    "site_types": dict(sorted(site_types.items())),
                    "nets": manifest["outputs"]["nets.jsonl"]["count"],
                    "pins": pins,
                    "connections": connections,
                    "timed_connections": timed_connections,
                    "heterogeneous_blocks": heterogeneous_blocks,
                    "cpu_golden_legal": True,
                    "cpu_golden_moved_blocks": 0,
                    "native_vpr_legal": True,
                    "native_macro_count": len(native_macro_ids),
                    "native_macro_members": native_macro_members,
                    "native_macro_hash_verified": True,
                    "native_matches_baseline": True,
                    "routing_iterations": native["routing_iterations"],
                    "wirelength": native["wirelength"],
                    "cpd_ns": native["cpd_ns"],
                    "vpr_revision": native["vpr_revision"],
                    "route_sha256": native["outputs"]["route"]["sha256"],
                }
            if case == "koios_conv_layer":
                probe = read_json(contract / "real_legalization_probe.json")
                recovered = read_json(contract / "recovered_vpr_native_closure.json")
                if probe.get("status") != "pass" or recovered.get("status") != "pass":
                    raise ValueError(f"{case}: illegal-placement recovery closure did not pass")
                if recovered["inputs"]["golden_place"]["sha256"] != probe["recovered_place"]["sha256"]:
                    raise ValueError(f"{case}: recovered placement hash differs from native closure input")
                row["recovery"] = {
                    "cpu_legal": probe["recovery"]["legal"],
                    "deterministic": probe["recovered_place"]["sha256"] == probe["repeat_sha256"],
                    "moved_from_input": probe["recovery"]["moved_from_input"],
                    "moved_from_reference": probe["recovery"]["moved_from_reference"],
                    "native_vpr_legal": recovered["legal"],
                    "routing_iterations": recovered["routing_iterations"],
                    "wirelength": recovered["wirelength"],
                    "cpd_ns": recovered["cpd_ns"],
                }
            rows.append(row)
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as error:
        print(f"prepare_correctness_matrix: ERROR: {error}", file=sys.stderr)
        return 2

    result = {
        "schema": "TILEPLACE_CORRECTNESS_MATRIX_V2",
        "status": "pass",
        "cases": rows,
        "summary": {
            "case_count": len(rows),
            "all_cpu_golden_legal": all(row["cpu_golden_legal"] for row in rows),
            "all_native_vpr_legal": all(row["native_vpr_legal"] for row in rows),
            "all_native_match_baseline": all(row["native_matches_baseline"] for row in rows),
            "all_native_macro_hashes_verified": all(row["native_macro_hash_verified"] for row in rows),
            "total_blocks": sum(row["blocks"] for row in rows),
            "total_connections": sum(row["connections"] for row in rows),
            "heterogeneous_case_count": sum(row["heterogeneous_blocks"] > 0 for row in rows),
            "heterogeneous_blocks": sum(row["heterogeneous_blocks"] for row in rows),
            "native_macro_count": sum(row["native_macro_count"] for row in rows),
            "native_macro_members": sum(row["native_macro_members"] for row in rows),
            "koios_recovery_native_vpr_legal": rows[-1]["recovery"]["native_vpr_legal"],
        },
        "limitations": [
            "CPU golden is a zero-displacement correctness reference, not a placement QoR improvement.",
            "The Koios case has routed connections but no imported per-connection timing criticality CSV yet.",
            "The five real cases contain no external region/fixed/macro constraint file; Koios contains VPR-native direct-chain macros.",
        ],
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
