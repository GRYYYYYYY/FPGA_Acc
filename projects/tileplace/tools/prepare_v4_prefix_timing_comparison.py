#!/usr/bin/env python3
"""Verify full-trace equivalence before reporting a paired CPU timing ratio."""

import argparse
import json
import statistics
from pathlib import Path

from prepare_tileplace_v4_heldout_matrix import verify_search_audit
from run_v4_timing_protocol import signature, feedback_signature
from tileplace_provenance import verify_files
from tileplace_vpr import ContractError, dump_json, sha256


PROTOCOL_SHA = "a74f8a943c876bccf385e169d67b253e39d0a3bae825146b57b09283196ade89"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    exp = Path(__file__).resolve().parents[1] / "experiments"
    protocol_path = exp / "tileplace_v4_prefix_timing_protocol_2026-09-29.json"
    if sha256(protocol_path) != PROTOCOL_SHA:
        raise ContractError("optimized protocol changed")
    protocol = json.loads(protocol_path.read_text())
    baseline_path = Path(protocol["paired_baseline"]["path"])
    if sha256(baseline_path) != protocol["paired_baseline"]["sha256"]:
        raise ContractError("paired baseline changed")
    baseline = json.loads(baseline_path.read_text())
    root = Path(protocol["output_root"])
    summary_path = root / "summary.json"
    optimized = json.loads(summary_path.read_text())
    if optimized["status"] != "pass" or optimized["protocol_sha256"] != PROTOCOL_SHA:
        raise ContractError("optimized timing protocol did not complete")
    baseline_report = json.loads(Path(protocol["reference_report"]).read_text())
    expected, expected_feedback = signature(baseline_report), feedback_signature(baseline_report)
    for row in optimized["runs"]:
        run = root / f"run_{row['index']:02d}"
        report_path = run / "report.json"
        if sha256(report_path) != row["report_sha256"] or sha256(run / "timing.json") != row["timing_sha256"]:
            raise ContractError("optimized observation changed")
        report = json.loads(report_path.read_text())
        if signature(report) != expected or feedback_signature(report) != expected_feedback:
            raise ContractError("optimized run changed decisions or feedback")
        if report["phases"] != baseline_report["phases"] or (
            [t["transactions"] for t in report["trials"]]
            != [t["transactions"] for t in baseline_report["trials"]]
        ):
            raise ContractError("optimized run changed proposal audits or transaction costs")
        verify_search_audit(report, "diffeq")
        if report["provenance"]["implementation"]["sha256"] != protocol["implementation_sha256"]:
            raise ContractError("optimized source identity mismatch")
        verify_files(report["provenance"]["inputs"])
        archive_path = exp / "implementation_sources" / protocol["implementation_sha256"] / "archive.json"
        archive = json.loads(archive_path.read_text())
        expected_sources = {(r["name"], r["sha256"]) for r in report["provenance"]["implementation"]["sources"]}
        if {(r["name"], r["sha256"]) for r in archive["sources"]} != expected_sources:
            raise ContractError("optimized archived source set differs")
        verify_files(archive["sources"])
    measured = [r for r in optimized["runs"] if not r["warmup"]]
    times = [r["process_wall_s"] for r in measured]
    if len(measured) != 3:
        raise ContractError("expected all three optimized observations")
    optimized_median = statistics.median(times)
    optimized_proposal = statistics.median(r["timing"]["search_stage_wall_s"]["proposal"] for r in measured)
    result = {
        "schema": "TILEPLACE_V4_PREFIX_PAIRED_TIMING_V1", "status": "pass", "case": "diffeq",
        "protocol_sha256": PROTOCOL_SHA,
        "baseline": {"path": str(baseline_path), "sha256": sha256(baseline_path),
                     "implementation_sha256": baseline["implementation_sha256"],
                     "median_process_wall_s": baseline["median_process_wall_s"],
                     "median_proposal_wall_s": baseline["median_stage_wall_s"]["proposal"]},
        "optimized": {"path": str(summary_path), "sha256": sha256(summary_path),
                      "implementation_sha256": protocol["implementation_sha256"],
                      "process_wall_samples_s": times, "median_process_wall_s": optimized_median,
                      "median_proposal_wall_s": optimized_proposal, "sample_cv_pct": optimized["sample_cv_pct"]},
        "process_median_ratio": baseline["median_process_wall_s"] / optimized_median,
        "proposal_median_ratio": baseline["median_stage_wall_s"]["proposal"] / optimized_proposal,
        "all_full_traces_and_feedback_equal": True,
        "final": expected["final"], "final_place_sha256": expected["final_place_sha256"],
        "limitations": protocol["limitations"] + ["Measurements sequential, not randomized/interleaved; natural cache on shared host", "Complete process boundary excludes precomputed inputs and baseline generation"],
    }
    dump_json(args.output, result)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
