#!/usr/bin/env python3
"""Inject a real region/fixed violation and audit deterministic CPU recovery."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tileplace_vpr import (
    ContractError,
    in_region,
    legalize,
    location,
    matches_fixed,
    parse_place,
    read_jsonl,
    sha256,
    validate_contract,
)


def write_place(path: Path, header: dict[str, str], rows: list[dict]) -> None:
    lines = [header["netlist"], header["array_size"], "", "#block name x y subblk layer block number"]
    for row in rows:
        lines.append(
            f"{row['name']} {row['x']} {row['y']} {row['subtile']} {row['layer']} #{row['block_number']}"
        )
    path.write_text("\n".join(lines) + "\n")


def swap_location(first: dict, second: dict) -> None:
    fields = ("x", "y", "subtile", "layer")
    saved = {field: first[field] for field in fields}
    for field in fields:
        first[field] = second[field]
        second[field] = saved[field]


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
        block_by_name = {block["name"]: block for block in blocks}
        header, original = parse_place(golden)
        original_by_name = {row["name"]: row for row in original}

        pair = None
        constrained = sorted(
            (block for block in blocks if block.get("region") is not None or block.get("fixed")),
            key=lambda block: (block["block_id"], block["name"]),
        )
        all_blocks = sorted(blocks, key=lambda block: (block["block_id"], block["name"]))
        for first in constrained:
            first_loc = location(original_by_name[first["name"]])
            for second in all_blocks:
                if first["name"] == second["name"] or first["logical_type"] != second["logical_type"]:
                    continue
                if first.get("macro") or second.get("macro"):
                    continue
                second_loc = location(original_by_name[second["name"]])
                first_violates = not in_region(first, second_loc) or not matches_fixed(first, second_loc)
                second_violates = not in_region(second, first_loc) or not matches_fixed(second, first_loc)
                if first_violates and (second_violates or not second.get("fixed")):
                    pair = (first, second, first_violates, second_violates)
                    break
            if pair is not None:
                break
        if pair is None:
            raise ContractError("no same-type location swap can violate an external constraint")

        first, second, first_violates, second_violates = pair
        corrupted = [dict(row) for row in original]
        row_by_name = {row["name"]: row for row in corrupted}
        swap_location(row_by_name[first["name"]], row_by_name[second["name"]])

        work = args.work.resolve()
        work.mkdir(parents=True, exist_ok=True)
        corrupted_path = work / "constraint_corrupted.place"
        recovered_a = work / "constraint_recovered_a.place"
        recovered_b = work / "constraint_recovered_b.place"
        write_place(corrupted_path, header, corrupted)
        rejection = None
        try:
            validate_contract(contract, corrupted_path)
        except ContractError as error:
            rejection = str(error)
        if rejection is None:
            raise ContractError("constraint-corrupted placement unexpectedly passed validation")
        if "violates region" not in rejection and "violates fixed dimensions" not in rejection:
            raise ContractError(f"validator rejected the probe for an unrelated reason: {rejection}")

        recovery_a = legalize(contract, recovered_a, corrupted_path)
        recovery_b = legalize(contract, recovered_b, corrupted_path)
        validate_contract(contract, recovered_a)
        if sha256(recovered_a) != sha256(recovered_b):
            raise ContractError("repeated constraint recovery produced different placements")
        if recovery_a["moved_from_input"] < 1:
            raise ContractError("constraint recovery did not move any injected block")

        report = {
            "schema": "TILEPLACE_EXTERNAL_CONSTRAINT_PROBE_V1",
            "status": "pass",
            "contract": str(contract),
            "golden_place_sha256": sha256(golden),
            "injection": {
                "kind": "same_type_location_swap",
                "blocks": [first["name"], second["name"]],
                "logical_type": first["logical_type"],
                "first_constraint_violation": first_violates,
                "second_constraint_violation": second_violates,
            },
            "validator_rejection": rejection,
            "corrupted_place": {"path": str(corrupted_path), "sha256": sha256(corrupted_path)},
            "recovered_place": {"path": str(recovered_a), "sha256": sha256(recovered_a)},
            "repeat_sha256": sha256(recovered_b),
            "recovery": recovery_a,
            "constraint_sources": {
                name: block_by_name[name].get("region") for name in (first["name"], second["name"])
            },
        }
        args.report.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.report.resolve().write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"status": "pass", **recovery_a, "recovered_sha256": sha256(recovered_a)}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"run_external_constraint_probe: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
