#!/usr/bin/env python3
"""Inject deterministic errors into a real contract and audit CPU recovery."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tileplace_vpr import ContractError, legalize, parse_place, read_jsonl, sha256, validate_contract


def write_place(path: Path, header: dict[str, str], rows: list[dict]) -> None:
    lines = [header["netlist"], header["array_size"], "", "#block name x y subblk layer block number"]
    for row in rows:
        lines.append(
            f"{row['name']} {row['x']} {row['y']} {row['subtile']} {row['layer']} #{row['block_number']}"
        )
    path.write_text("\n".join(lines) + "\n")


def copy_location(target: dict, source: dict) -> None:
    for field in ("x", "y", "subtile", "layer"):
        target[field] = source[field]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--golden-place", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        contract = args.contract.resolve()
        golden = args.golden_place.resolve()
        validate_contract(contract, golden)
        blocks = read_jsonl(contract / "blocks.jsonl")
        header, original = parse_place(golden)
        row_index = {row["name"]: index for index, row in enumerate(original)}
        clbs = [block for block in blocks if block["logical_type"] == "clb"]
        dsps = [block for block in blocks if block["logical_type"] == "dsp_top"]
        memories = [block for block in blocks if block["logical_type"] == "memory"]
        if len(clbs) < 3 or not dsps or not memories:
            raise ContractError("probe requires at least three CLBs, one DSP, and one memory block")

        corrupted = [dict(row) for row in original]
        clb0 = corrupted[row_index[clbs[0]["name"]]]
        clb1 = corrupted[row_index[clbs[1]["name"]]]
        clb2 = corrupted[row_index[clbs[2]["name"]]]
        dsp = corrupted[row_index[dsps[0]["name"]]]
        memory = corrupted[row_index[memories[0]["name"]]]
        copy_location(clb1, clb0)
        clb2_location = {field: clb2[field] for field in ("x", "y", "subtile", "layer")}
        copy_location(clb2, dsp)
        for field, value in clb2_location.items():
            dsp[field] = value
        memory["y"] += 1

        work = args.work.resolve()
        work.mkdir(parents=True, exist_ok=True)
        corrupted_path = work / "corrupted.place"
        recovered_a = work / "recovered_a.place"
        recovered_b = work / "recovered_b.place"
        write_place(corrupted_path, header, corrupted)
        rejection = None
        try:
            validate_contract(contract, corrupted_path)
        except ContractError as error:
            rejection = str(error)
        if rejection is None:
            raise ContractError("corrupted placement unexpectedly passed validation")

        recovery_a = legalize(contract, recovered_a, corrupted_path)
        recovery_b = legalize(contract, recovered_b, corrupted_path)
        validate_contract(contract, recovered_a)
        if sha256(recovered_a) != sha256(recovered_b):
            raise ContractError("repeated recovery produced different placements")
        if recovery_a["moved_from_input"] < 4:
            raise ContractError("recovery did not repair all injected error classes")

        report = {
            "schema": "TILEPLACE_REAL_LEGALIZATION_PROBE_V1",
            "status": "pass",
            "contract": str(contract),
            "golden_place_sha256": sha256(golden),
            "corrupted_place": {"path": str(corrupted_path), "sha256": sha256(corrupted_path)},
            "recovered_place": {"path": str(recovered_a), "sha256": sha256(recovered_a)},
            "repeat_sha256": sha256(recovered_b),
            "validator_rejection": rejection,
            "injections": [
                {"kind": "duplicate_occupancy", "blocks": [clbs[0]["name"], clbs[1]["name"]]},
                {"kind": "clb_dsp_type_swap", "blocks": [clbs[2]["name"], dsps[0]["name"]]},
                {"kind": "memory_non_root_offset", "blocks": [memories[0]["name"]]},
            ],
            "recovery": recovery_a,
        }
        args.report.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.report.resolve().write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"status": "pass", **recovery_a, "recovered_sha256": sha256(recovered_a)}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"run_real_legalization_probe: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
