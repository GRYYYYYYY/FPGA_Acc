#!/usr/bin/env python3
"""Read-only comparison of archived V4 feedback summaries and parser variants."""

import argparse
import json
import re
from pathlib import Path

import prepare_timing_feedback as feedback
from run_tileplace_v2 import timing_report_for_closure
from tileplace_vpr import ContractError, dump_json, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    exp = project / "experiments"
    current = feedback.POINT
    variants = {"current_any_indexed_port": current,
                "diagnostic_legacy_named_ports": re.compile(r"^\s*(\S+)\.(?:in|out|Q|D|clk)\[\d+\]")}
    rows = []
    for cohort, matrix_path in (
        ("development", exp / "tileplace_v4_development_matrix_2026-09-03.json"),
        ("heldout", exp / "tileplace_v4_heldout_matrix_2026-09-05.json"),
    ):
        for case in json.loads(matrix_path.read_text())["cases"]:
            name = case["case"]
            report_path = Path(case["report"]["path"])
            if sha256(report_path) != case["report"]["sha256"]:
                raise ContractError(f"search report changed: {name}")
            report = json.loads(report_path.read_text())
            if cohort == "development":
                base_dir = exp / f"{name}_seed1_cw200"
                contract = exp / f"{name}_seed1_cw200_endpoints"
            else:
                base_dir = (project / "work/tileplace_v4_heldout" if name in {"pdc", "dsip"}
                            else exp / "tileplace_v4_heldout_inputs") / name
                contract = exp / "tileplace_v4_heldout_inputs" / f"{name}_endpoints"
            base = json.loads((base_dir / "vpr_native_closure.json").read_text())
            timing = timing_report_for_closure(base)
            archived = report["initial_timing_feedback"]
            if sha256(timing) != archived["timing_report_sha256"]:
                raise ContractError(f"baseline timing changed: {name}")
            variants_result = {}
            try:
                for label, pattern in variants.items():
                    feedback.POINT = pattern
                    try:
                        payload = feedback.prepare(timing, Path(base["inputs"]["netlist"]["path"]), contract / "blocks.jsonl", 20)
                    except ContractError as error:
                        variants_result[label] = {"error": str(error), "matches_archived_summary": False}
                        continue
                    summary = {"edge_count": len(payload["edges"]), "focus_blocks": len(payload["focus_blocks"]),
                               "parsed_paths": payload["parsed_paths"], "timing_report_sha256": sha256(timing)}
                    variants_result[label] = {"summary": summary, "matches_archived_summary": summary == archived}
            finally:
                feedback.POINT = current
            rows.append({"case": name, "cohort": cohort, "report": case["report"],
                         "archived_summary": archived, "variants": variants_result})
            print(name, {k: (v.get("summary", {}).get("edge_count", "parse_error"), v["matches_archived_summary"]) for k, v in variants_result.items()}, flush=True)
    dump_json(args.output, {"schema": "TILEPLACE_V4_TIMING_PARSER_AUDIT_V1", "status": "audit_complete",
                           "current_parser_sha256": sha256(Path(feedback.__file__)), "cases": rows,
                           "scope": "Initial-feedback counts only; count equality does not establish identical edge identities or full search equivalence",
                           "finding": "Do not infer a single frozen implementation from config/VPR hashes alone; parser behavior must also be pinned."})


if __name__ == "__main__":
    main()
