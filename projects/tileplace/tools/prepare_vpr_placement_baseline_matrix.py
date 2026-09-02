#!/usr/bin/env python3
"""Audit VPR placement reports and compare conventional, analytic, and TilePlace QoR."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def delta_pct(value: float, reference: float) -> float:
    return (value / reference - 1.0) * 100.0


def geomean_delta(values: list[float], references: list[float]) -> float:
    return (math.exp(sum(math.log(value / reference) for value, reference in zip(values, references)) / len(values)) - 1) * 100


def audit_output_hashes(report: dict, label: str) -> None:
    for name, record in report["outputs"].items():
        path = Path(record["path"])
        require(path.is_file(), f"{label}: missing output {name}: {path}")
        require(sha256(path) == record["sha256"], f"{label}: output hash mismatch for {name}")


def aggregate(rows: list[dict], method: str) -> dict:
    wirelengths = [row[method]["wirelength"] for row in rows]
    cpds = [row[method]["cpd_ns"] for row in rows]
    references_wl = [row["conventional"]["wirelength"] for row in rows]
    references_cpd = [row["conventional"]["cpd_ns"] for row in rows]
    wl_deltas = [delta_pct(value, reference) for value, reference in zip(wirelengths, references_wl)]
    cpd_deltas = [delta_pct(value, reference) for value, reference in zip(cpds, references_cpd)]
    return {
        "cases": len(rows),
        "wirelength_geomean_delta_pct": geomean_delta(wirelengths, references_wl),
        "cpd_geomean_delta_pct": geomean_delta(cpds, references_cpd),
        "wirelength_improved_cases": sum(value < 0 for value in wl_deltas),
        "cpd_nonregressing_cases": sum(value <= 1e-12 for value in cpd_deltas),
        "wirelength_worst_delta_pct": max(wl_deltas),
        "cpd_worst_delta_pct": max(cpd_deltas),
    }


def compact(report: dict, reference: dict | None = None) -> dict:
    result = {
        "wirelength": report["wirelength"],
        "cpd_ns": report["cpd_ns"],
        "routing_iterations": report["routing_iterations"],
        "placement_stage_s": report["stage_times_s"]["placement"],
        "vpr_entire_flow_s": report["stage_times_s"]["vpr_entire_flow"],
        "wall_s": report["wall_s"],
        "moved_from_reference": report["placement"]["moved_from_reference"],
        "place_sha256": report["outputs"]["place"]["sha256"],
        "route_sha256": report["outputs"]["route"]["sha256"],
    }
    if reference is not None:
        result["wirelength_delta_pct"] = delta_pct(report["wirelength"], reference["wirelength"])
        result["cpd_delta_pct"] = delta_pct(report["cpd_ns"], reference["cpd_ns"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--tileplace-matrix", type=Path, required=True)
    parser.add_argument("--build-provenance", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    config_path = args.config.resolve()
    reports_dir = args.reports.resolve()
    tileplace_path = args.tileplace_matrix.resolve()
    build_path = args.build_provenance.resolve()
    config = load(config_path)
    tileplace = load(tileplace_path)
    build = load(build_path)
    require(config["schema"] == "TILEPLACE_VPR_PLACEMENT_BASELINE_CASES_V1", "unexpected case schema")
    require(tileplace["schema"] == "TILEPLACE_TIMING_MULTICASE_MATRIX_V2", "unexpected TilePlace matrix schema")
    require(build["schema"] == "TILEPLACE_VPR_EIGEN_BUILD_V1", "unexpected VPR build schema")
    require(build["status"] == "pass", "VPR build provenance did not pass")
    require(build["binary"]["sha256"] == config["vpr_sha256"], "build/config VPR hash mismatch")
    require(build["revision_validation"]["vpr_reported"] == config["vpr_revision"], "build/config revision mismatch")
    require(build["analytic_placer_evidence"]["status"] == "enabled", "build lacks analytic placer evidence")
    tileplace_by_case = {row["case"]: row for row in tileplace["cases"]}
    expected_cases = [row["case"] for row in config["cases"]]
    require(set(tileplace_by_case) == set(expected_cases), "TilePlace and VPR baseline case sets differ")

    rows = []
    report_records = {}
    for case_config in config["cases"]:
        case = case_config["case"]
        reports = {}
        for mode in ("conventional", "analytic"):
            path = reports_dir / f"{case}_{mode}.json"
            require(path.is_file(), f"missing {case} {mode} report")
            report = load(path)
            label = f"{case} {mode}"
            require(report["schema"] == "TILEPLACE_VPR_PLACEMENT_BASELINE_V1", f"{label}: wrong schema")
            require(report["status"] == "pass" and report["legal"], f"{label}: run is not legal/pass")
            require(report["case"] == case and report["mode"] == mode, f"{label}: identity mismatch")
            require(report["same_packed_netlist"], f"{label}: same-netlist assertion is false")
            require(not report["integrated_analytical_place"], f"{label}: integrated AP is not comparable")
            require(report["num_workers"] == 1, f"{label}: run is not single-worker")
            require(report["seed"] == case_config["seed"], f"{label}: seed mismatch")
            require(report["channel_width"] == case_config["channel_width"], f"{label}: channel width mismatch")
            tool = report["tool_validation"]
            require(tool["vpr_revision"] == config["vpr_revision"], f"{label}: revision mismatch")
            require(report["inputs"]["vpr"]["sha256"] == config["vpr_sha256"], f"{label}: VPR hash mismatch")
            require(tool["analytic_enabled"] == (mode == "analytic"), f"{label}: AP enable mismatch")
            require(tool["analytic_option_available"], f"{label}: AP option unavailable")
            markers = tool["analytic_execution_markers"]
            require(all(markers.values()) == (mode == "analytic"), f"{label}: AP execution marker mismatch")
            require(report["placement_validation"]["legal"], f"{label}: contract validation failed")
            audit_output_hashes(report, label)
            reports[mode] = report
            report_records[f"{case}_{mode}"] = {"path": str(path), "sha256": sha256(path)}

        conventional = reports["conventional"]
        analytic = reports["analytic"]
        for key in ("vpr", "architecture", "circuit", "packed_netlist", "reference_place"):
            require(
                conventional["inputs"][key]["sha256"] == analytic["inputs"][key]["sha256"],
                f"{case}: paired {key} hash mismatch",
            )
        require(conventional["placement"]["moved_from_reference"] == 0, f"{case}: conventional placement not reproduced")
        tp = tileplace_by_case[case]
        require(conventional["wirelength"] == tp["baseline"]["wirelength"], f"{case}: baseline WL mismatch")
        require(conventional["cpd_ns"] == tp["baseline"]["cpd_ns"], f"{case}: baseline CPD mismatch")
        require(
            conventional["routing_iterations"] == tp["baseline"]["routing_iterations"],
            f"{case}: baseline routing iteration mismatch",
        )
        tileplace_result = {
            "wirelength": tp["candidate"]["wirelength"],
            "cpd_ns": tp["candidate"]["cpd_ns"],
            "routing_iterations": tp["candidate"]["routing_iterations"],
            "wirelength_delta_pct": tp["candidate"]["wirelength_delta_pct"],
            "cpd_delta_pct": tp["candidate"]["cpd_delta_pct"],
            "moved_from_reference": tp["accepted_moves"],
            "place_sha256": tp["deterministic_output_sha256"],
        }
        rows.append(
            {
                "case": case,
                "cohort": tp["cohort"],
                "same_router": True,
                "same_packed_netlist": True,
                "conventional": compact(conventional),
                "analytic": compact(analytic, conventional),
                "tileplace": tileplace_result,
            }
        )

    analytic_aggregate = aggregate(rows, "analytic")
    tileplace_aggregate = aggregate(rows, "tileplace")
    for key in ("wirelength_geomean_delta_pct", "cpd_geomean_delta_pct"):
        require(abs(tileplace_aggregate[key] - tileplace["aggregate"][key]) < 1e-12, f"TilePlace {key} mismatch")
    output = {
        "schema": "TILEPLACE_VPR_PLACEMENT_BASELINE_MATRIX_V1",
        "status": "pass",
        "methodology": {
            "comparison": "same packed netlist, architecture, atom netlist, seed, channel width, VPR revision/binary, single-worker router and analysis",
            "conventional": "VPR timing-driven simulated annealing plus quench",
            "analytic": "VPR cluster-level --enable_analytic_placer true plus quench; not integrated --analytical_place",
            "tileplace": "frozen deterministic post-placement 2x2-page refinement of the conventional placement",
        },
        "aggregate": {
            "analytic_vs_conventional": analytic_aggregate,
            "tileplace_vs_conventional": tileplace_aggregate,
        },
        "cases": rows,
        "inputs": {
            "case_config": {"path": str(config_path), "sha256": sha256(config_path)},
            "build_provenance": {"path": str(build_path), "sha256": sha256(build_path)},
            "tileplace_matrix": {"path": str(tileplace_path), "sha256": sha256(tileplace_path)},
            "reports": report_records,
            "vpr_revision": config["vpr_revision"],
            "vpr_sha256": config["vpr_sha256"],
        },
        "claim_boundary": "All values are CPU VPR placement/route/analysis or deterministic CPU TilePlace refinement results, not FPGA hardware performance. Placement and entire-flow times are single-run audit metadata, not a runtime benchmark. VPR cluster-level AP is an official experimental wirelength-oriented path and is reported even where routed QoR regresses.",
    }
    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output["aggregate"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
