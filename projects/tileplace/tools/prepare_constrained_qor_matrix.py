#!/usr/bin/env python3
"""Audit the separately reported post-freeze fixed-I/O TilePlace QoR point."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from tileplace_vpr import ContractError, dump_json, sha256


def load(path: Path) -> dict:
    if not path.is_file():
        raise ContractError(f"missing evidence: {path}")
    return json.loads(path.read_text())


def delta(candidate: float, baseline: float) -> float:
    return (candidate / baseline - 1.0) * 100.0


def require_option(command: list[str], option: str, expected: str) -> None:
    if command.count(option) != 1:
        raise ContractError(f"expected exactly one {option} in VPR command")
    index = command.index(option)
    if index + 1 >= len(command) or command[index + 1] != expected:
        raise ContractError(f"unexpected {option} value")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tileplace", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        root = args.tileplace.resolve()
        experiments = root / "experiments"
        work = root / "work"
        source_dir = experiments / "apex4_fixed_io_seed1_cw78_v2"
        endpoint_dir = experiments / "apex4_fixed_io_seed1_cw78_endpoints"
        capture_dir = work / "apex4_fixed_io_constrained_qor_2026-09-01"
        prereg_path = experiments / "apex4_fixed_io_constrained_qor_preregistration_2026-09-01.json"
        prereg = load(prereg_path)
        manifest_path = endpoint_dir / "manifest.json"
        manifest = load(manifest_path)
        cpu_path = endpoint_dir / "page2_connection_star_guard_q60000_w1.json"
        cpu = load(cpu_path)
        candidate_place = endpoint_dir / "page2_connection_star_guard_q60000_w1.place"
        candidate_path = endpoint_dir / "page2_connection_star_guard_q60000_w1_vpr_native.json"
        candidate = load(candidate_path)
        baseline_path = source_dir / "vpr_native_closure.json"
        baseline = load(baseline_path)
        repeat_path = capture_dir / "page2_repeat.json"
        repeat_place = capture_dir / "page2_repeat.place"
        timing_path = capture_dir / "reference_timing.output.csv"
        connections_path = capture_dir / "connections.csv"
        timing_log = Path(str(timing_path) + ".vpr.log")

        for label, evidence in (("baseline", baseline), ("cpu", cpu), ("candidate", candidate)):
            if evidence.get("status") != "pass" or evidence.get("legal", True) is not True:
                raise ContractError(f"{label} evidence is not passing")
        if prereg.get("status") != "preregistered_before_timing_capture_or_tileplace_qor_run":
            raise ContractError("constrained QoR point was not preregistered")
        if prereg.get("cohort") != "constrained_post_freeze_validation":
            raise ContractError("unexpected constrained QoR cohort")

        mapping = manifest.get("connection_endpoint_mapping", {})
        expected_connections = 2263
        for key in ("connections", "mapped_sources", "mapped_sinks", "timed_connections",
                    "timed_fully_mapped", "atom_timing_pin_labeled", "atom_timing_pin_mapped"):
            if mapping.get(key) != expected_connections:
                raise ContractError(f"incomplete endpoint/timing mapping: {key}")
        if mapping.get("atom_timing_pin_unmapped") != 0:
            raise ContractError("unexpected unmapped atom timing pins")
        constraints = manifest.get("placement_constraints", {})
        if constraints.get("coordinate_fixed_clusters") != 28 or constraints.get("source") != "vpr_constraints_xml":
            raise ContractError("fixed-I/O constraint accounting differs")

        expected_strategy = prereg["frozen_tileplace_strategy"]
        observed_strategy = {
            "page_size": [cpu["page_width"], cpu["page_height"]],
            "passes": 8,
            "candidate_limit": cpu["candidate_limit"],
            "wire_weight": cpu["wire_weight"],
            "timing_weight": cpu["timing_weight"],
            "timing_model": cpu["timing_model"],
            "critical_distance_guard_q": cpu["critical_distance_guard_q"],
            "critical_distance_slack": cpu["critical_distance_slack"],
            "proposal_workers": cpu["proposal_workers"],
        }
        if observed_strategy != expected_strategy:
            raise ContractError("frozen TilePlace strategy differs from preregistration")
        if len(cpu["passes"]) > 8 or cpu["guarded_connections_increased"] != 0:
            raise ContractError("CPU guard/pass accounting differs")
        if cpu["timed_connections"] != expected_connections or cpu["timing_mapping_coverage"] != 1.0:
            raise ContractError("CPU timing coverage differs")
        if sha256(candidate_place) != cpu["output_place_sha256"]:
            raise ContractError("candidate placement hash differs from CPU report")
        if candidate_place.read_bytes() != repeat_place.read_bytes() or cpu_path.read_bytes() != repeat_path.read_bytes():
            raise ContractError("complete CPU repeat is not byte-identical")

        timing_rows = 0
        timing_mapped = 0
        guarded_rows = 0
        cpd_ps: set[int] = set()
        with timing_path.open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                timing_rows += 1
                timing_mapped += int(row["timing_pin_mapped"])
                guarded_rows += int(row["criticality_q"]) >= 60000
                cpd_ps.add(int(row["critical_path_delay_ps"]))
        if (timing_rows, timing_mapped, guarded_rows, cpd_ps) != (
            expected_connections, expected_connections, cpu["guarded_connections"], {5202}
        ):
            raise ContractError("timing-export accounting differs")
        if "VPR succeeded" not in timing_log.read_text(errors="replace"):
            raise ContractError("timing-export VPR did not succeed")

        source = prereg["source_inputs"]
        if manifest["inputs"]["architecture"]["sha256"] != source["architecture_sha256"]:
            raise ContractError("architecture hash differs from preregistration")
        if manifest["inputs"]["packed_netlist"]["sha256"] != source["packed_netlist_sha256"]:
            raise ContractError("packed-netlist hash differs from preregistration")
        if manifest["inputs"]["reference_place"]["sha256"] != source["placement_sha256"]:
            raise ContractError("reference-placement hash differs from preregistration")
        if manifest["inputs"]["rr_graph"]["sha256"] != source["rr_graph_sha256"]:
            raise ContractError("RR-graph hash differs from preregistration")
        if manifest["inputs"]["vpr_constraints"]["sha256"] != source["vpr_constraints_sha256"]:
            raise ContractError("constraint hash differs from preregistration")

        frozen = prereg["frozen_binaries"]
        for closure in (baseline, candidate):
            if closure["inputs"]["vpr"]["sha256"] != frozen["correctness_vpr_sha256"]:
                raise ContractError("QoR closure did not use the frozen correctness VPR")
            if closure["vpr_revision"] != prereg["source_baseline"]["vpr_revision"]:
                raise ContractError("QoR closure VPR revision differs")
            if closure["seed"] != 1 or closure["channel_width"] != 78:
                raise ContractError("QoR closure seed/channel width differs")
            require_option(closure["command"], "--device", "mcnc_medium")
            require_option(
                closure["command"], "--read_vpr_constraints",
                str((source_dir / "source.vpr_constraints.xml").resolve()),
            )
        timing_vpr = root / (
            "third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/"
            "build_tileplace_vpr_timing_optional/vpr/vpr"
        )
        if sha256(timing_vpr) != frozen["timing_export_vpr_sha256"]:
            raise ContractError("timing-export VPR hash differs")

        source_baseline = prereg["source_baseline"]
        if (baseline["wirelength"], baseline["cpd_ns"], baseline["routing_iterations"]) != (
            source_baseline["wirelength"], source_baseline["cpd_ns"], source_baseline["routing_iterations"]
        ):
            raise ContractError("native baseline does not reproduce preregistered QoR")
        if candidate["placement_validation"]["blocks"] != 110:
            raise ContractError("candidate native placement validation differs")

        report = {
            "schema": "TILEPLACE_CONSTRAINED_QOR_MATRIX_V1",
            "status": "pass",
            "date": "2026-09-01",
            "case": "apex4_fixed_io_seed1_cw78",
            "cohort": "constrained_post_freeze_validation",
            "separate_from": [
                "nine-case unconstrained TilePlace QoR aggregate",
                "six-case Eigen conventional/AP aggregate",
            ],
            "frozen_strategy": observed_strategy,
            "constraints": {
                "source": "native VPR XML",
                "coordinate_fixed_clusters": 28,
                "fixed_clusters_preserved": 28,
            },
            "endpoint_mapping": mapping,
            "timing_export": {
                "connections": timing_rows,
                "atom_timing_pin_mapped": timing_mapped,
                "criticality_q_at_least_60000": guarded_rows,
                "critical_path_delay_ps": 5202,
            },
            "cpu": {
                "accepted_moves": cpu["accepted_moves"],
                "guarded_connections": cpu["guarded_connections"],
                "guarded_connections_increased": cpu["guarded_connections_increased"],
                "internal_hpwl": [cpu["initial_wire_hpwl"], cpu["final_wire_hpwl"]],
                "internal_timing_cost_q": [cpu["initial_timing_hpwl_q"], cpu["final_timing_hpwl_q"]],
                "deterministic_output_sha256": cpu["output_place_sha256"],
                "complete_repeat_byte_identical": True,
            },
            "baseline": {
                "wirelength": baseline["wirelength"],
                "cpd_ns": baseline["cpd_ns"],
                "routing_iterations": baseline["routing_iterations"],
            },
            "candidate": {
                "wirelength": candidate["wirelength"],
                "cpd_ns": candidate["cpd_ns"],
                "routing_iterations": candidate["routing_iterations"],
                "wirelength_delta_pct": delta(candidate["wirelength"], baseline["wirelength"]),
                "cpd_delta_pct": delta(candidate["cpd_ns"], baseline["cpd_ns"]),
            },
            "decision": "retain_separate_constrained_negative_qor_point",
            "claim_boundary": (
                "This point proves that the frozen TilePlace flow preserves native coordinate-fixed I/O "
                "through deterministic CPU refinement and VPR route/analysis. Its small routed-WL and CPD "
                "regressions are retained. It is not part of the unconstrained QoR or Eigen AP aggregates."
            ),
            "evidence": {
                "preregistration": {"path": str(prereg_path), "sha256": sha256(prereg_path)},
                "manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)},
                "connections": {"path": str(connections_path), "sha256": sha256(connections_path)},
                "timing": {"path": str(timing_path), "sha256": sha256(timing_path)},
                "cpu": {"path": str(cpu_path), "sha256": sha256(cpu_path)},
                "baseline_closure": {"path": str(baseline_path), "sha256": sha256(baseline_path)},
                "candidate_closure": {"path": str(candidate_path), "sha256": sha256(candidate_path)},
            },
        }
        dump_json(args.output.resolve(), report)
        print(json.dumps({"status": "pass", "case": report["case"], **report["candidate"]}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError, csv.Error) as error:
        print(f"prepare_constrained_qor_matrix: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
