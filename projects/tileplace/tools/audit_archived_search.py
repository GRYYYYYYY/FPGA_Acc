#!/usr/bin/env python3
"""Audit completed search matrices using sealed sources, not live source paths.

This verifies archived search evidence and repeat identity. It does not replace
the original protocol audit or establish historical blindness.
"""
import argparse
import json
from pathlib import Path

from audit_fixed_development import audit_native_trials
from prepare_tileplace_v4_heldout_matrix import verify_search_audit
from run_v4_timing_protocol import feedback_signature, signature
from tileplace_provenance import verify_files
from tileplace_vpr import ContractError, dump_json, sha256
from verify_archived_implementation import verify_archive


def audit(matrix_path, archive_root):
    raw = matrix_path.read_bytes()
    matrix = json.loads(raw)
    if matrix.get("status") != "pass":
        raise ContractError("matrix is not complete and passing")
    rows = []
    names = set()
    for case in matrix["cases"]:
        if case["case"] in names or not case["reports"]:
            raise ContractError("duplicate case or missing reports")
        names.add(case["case"])
        reference = None
        count = 0
        for receipt in case["reports"]:
            path = Path(receipt["path"])
            if sha256(path) != receipt["sha256"]:
                raise ContractError("search report changed")
            report = json.loads(path.read_text())
            implementation = report["provenance"]["implementation"]
            if report["status"] != "pass" or implementation["sha256"] != matrix["implementation_sha256"]:
                raise ContractError("search status or implementation mismatch")
            verify_archive(implementation, archive_root)
            verify_search_audit(report, case["case"])
            verify_files(report["provenance"]["inputs"])
            if sha256(Path(report["output_place"]["path"])) != report["output_place"]["sha256"]:
                raise ContractError("final placement changed")
            if any(t["closure"].get("status") != "pass" or t["closure"].get("legal") is not True for t in report["trials"]):
                raise ContractError("native trial failed")
            count += audit_native_trials(report)
            current = (signature(report), feedback_signature(report), report["phases"],
                       [t["transactions"] for t in report["trials"]])
            if reference is None:
                reference, first = current, report
            elif current != reference:
                raise ContractError("repeat trajectory differs")
        if len(case["reports"]) != case["repeat_count"]:
            raise ContractError("repeat count mismatch")
        for key, metric in (("cpd_ratio", "cpd_ns"), ("wirelength_ratio", "wirelength")):
            if case[key] != first["final"][metric] / first["baseline"][metric]:
                raise ContractError("matrix metric differs from report")
        rows.append({"case": case["case"], "reports": len(case["reports"]),
                     "verified_native_trials": count, "all_repeats_exact": True})
    import hashlib
    return {"schema": "TILEPLACE_ARCHIVED_SEARCH_AUDIT_V1", "status": "pass",
            "matrix": {"path": str(matrix_path), "sha256": hashlib.sha256(raw).hexdigest()},
            "implementation_sha256": matrix["implementation_sha256"], "cases": rows,
            "verified_native_trials": sum(r["verified_native_trials"] for r in rows),
            "scope": "Archived source and search artifacts; not an independent protocol or blindness audit"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, default=Path(__file__).resolve().parents[1] / "experiments" / "implementation_sources")
    args = parser.parse_args()
    result = audit(args.matrix, args.archive_root)
    dump_json(args.output, result)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
