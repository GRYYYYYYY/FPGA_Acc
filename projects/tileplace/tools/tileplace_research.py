#!/usr/bin/env python3
"""CPU research prototype for page-decomposed incremental TilePlace moves."""

from __future__ import annotations

import argparse
import json
import multiprocessing
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from tileplace_vpr import (
    ContractError,
    dump_json,
    in_region,
    load_contract,
    location,
    matches_fixed,
    parse_place,
    sha256,
    validate_contract,
)


_FORK_PROPOSAL_EVALUATOR: Any = None


def _evaluate_fork_chunk(
    payload: tuple[
        list[tuple[int, ...]],
        dict[int, tuple[int, int, int, int]],
        dict[tuple[int, int, int, int], int],
    ]
) -> list[tuple[Any, int, int, int, int]]:
    if _FORK_PROPOSAL_EVALUATOR is None:
        raise RuntimeError("fork proposal evaluator is not initialized")
    chunk, active_positions, active_occupied = payload
    return [
        _FORK_PROPOSAL_EVALUATOR(unit, active_positions, active_occupied)
        for unit in chunk
    ]


def page_key(loc: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int]:
    return loc[3], loc[0] // width, loc[1] // height


def hpwl(members: list[int], positions: dict[int, tuple[int, int, int, int]]) -> int:
    if len(members) < 2:
        return 0
    xs = [positions[block_id][0] for block_id in members]
    ys = [positions[block_id][1] for block_id in members]
    return max(xs) - min(xs) + max(ys) - min(ys)


def manhattan(
    source_id: int,
    sink_id: int,
    positions: dict[int, tuple[int, int, int, int]],
) -> int:
    source = positions[source_id]
    sink = positions[sink_id]
    return abs(source[0] - sink[0]) + abs(source[1] - sink[1])


def write_place(path: Path, header: dict[str, str], blocks: list[dict[str, Any]], positions: dict[int, tuple[int, int, int, int]]) -> None:
    lines = []
    if header.get("netlist"):
        lines.append(header["netlist"])
    if header.get("array_size"):
        lines.append(header["array_size"])
    lines.extend(["", "#block name\tx\ty\tsubblk\tlayer\tblock number", "#----------\t--\t--\t------\t-----\t------------"])
    for block in sorted(blocks, key=lambda item: (item["block_id"], item["name"])):
        x, y, subtile, layer = positions[block["block_id"]]
        lines.append(f"{block['name']}\t\t{x}\t{y}\t{subtile}\t{layer}\t#{block['block_id']}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def optimize(
    contract: Path,
    input_place: Path,
    output_place: Path,
    page_width: int,
    page_height: int,
    passes: int,
    candidate_limit: int,
    wire_weight: int,
    timing_weight: int,
    timing_model: str,
    critical_distance_guard_q: int,
    critical_distance_slack: int,
    max_wire_delta: int | None,
    max_connection_wire_delta: int | None,
    proposal_workers: int,
    eager_disabled_guard_costs: bool,
) -> dict[str, Any]:
    manifest, blocks, sites, nets = load_contract(contract)
    validate_contract(contract, input_place)
    header, rows = parse_place(input_place)
    row_by_name = {row["name"]: row for row in rows}
    block_by_id = {block["block_id"]: block for block in blocks}
    positions = {block["block_id"]: location(row_by_name[block["name"]]) for block in blocks}
    site_by_loc = {location(site): site for site in sites}
    sites_by_page_type: dict[tuple[tuple[int, int, int], str], list[tuple[int, int, int, int]]] = defaultdict(list)
    for site in sites:
        loc = location(site)
        sites_by_page_type[(page_key(loc, page_width, page_height), site["physical_type"])].append(loc)
    for values in sites_by_page_type.values():
        values.sort(key=lambda loc: (loc[3], loc[1], loc[0], loc[2]))

    net_members: dict[int, list[int]] = {}
    net_criticality: dict[int, int] = {}
    connection_timing: dict[int, list[tuple[int, int, int]]] = defaultdict(list)
    timed_connections = 0
    mapped_timed_connections = 0
    block_nets: dict[int, set[int]] = defaultdict(set)
    for net in nets:
        members = sorted({pin["block_id"] for pin in net["pins"] if pin["block_id"] in block_by_id})
        if len(members) < 2:
            continue
        net_id = net["net_id"]
        net_members[net_id] = members
        net_criticality[net_id] = max(0, int(net.get("criticality_q", 0)))
        for connection in net.get("connections", []):
            if "criticality_q" not in connection:
                continue
            timed_connections += 1
            if "source_block_id" in connection and "sink_block_id" in connection:
                connection_timing[net_id].append(
                    (
                        int(connection["source_block_id"]),
                        int(connection["sink_block_id"]),
                        max(0, int(connection["criticality_q"])),
                    )
                )
                mapped_timed_connections += 1
        for block_id in members:
            block_nets[block_id].add(net_id)

    macro_groups: dict[str, list[int]] = defaultdict(list)
    independent = []
    for block in blocks:
        if block.get("macro"):
            macro_groups[block["macro"]["id"]].append(block["block_id"])
        else:
            independent.append(block["block_id"])
    units = [tuple(sorted(members)) for _macro, members in sorted(macro_groups.items())]
    units.extend((block_id,) for block_id in sorted(independent))
    units.sort(key=lambda unit: (unit[0], len(unit), unit))

    if timing_model == "connection_star" and not connection_timing:
        raise ContractError("connection_star timing requested but the contract has no mapped endpoints")
    if max_connection_wire_delta is not None and not connection_timing:
        raise ContractError("connection wire guard requested but the contract has no mapped endpoints")

    guarded_connections: dict[int, list[tuple[int, int, int, int]]] = defaultdict(list)
    if critical_distance_guard_q > 0:
        if not connection_timing:
            raise ContractError("critical distance guard requested but the contract has no mapped endpoints")
        for net_id, connections in connection_timing.items():
            for source_id, sink_id, criticality_q in connections:
                if criticality_q >= critical_distance_guard_q:
                    guarded_connections[net_id].append(
                        (
                            source_id,
                            sink_id,
                            criticality_q,
                            manhattan(source_id, sink_id, positions),
                        )
                    )

    def timing_cost(net_id: int, candidate_positions: dict[int, tuple[int, int, int, int]]) -> int:
        if timing_model == "connection_star" and connection_timing.get(net_id):
            total = 0
            for source_id, sink_id, criticality_q in connection_timing[net_id]:
                total += criticality_q * manhattan(source_id, sink_id, candidate_positions)
            return total
        return net_criticality[net_id] * hpwl(net_members[net_id], candidate_positions)

    def net_objective(net_id: int, candidate_positions: dict[int, tuple[int, int, int, int]]) -> int:
        return (
            wire_weight * hpwl(net_members[net_id], candidate_positions)
            + timing_weight * timing_cost(net_id, candidate_positions)
        )

    def connection_wire_cost(
        net_id: int, candidate_positions: dict[int, tuple[int, int, int, int]]
    ) -> int:
        return sum(
            manhattan(source_id, sink_id, candidate_positions)
            for source_id, sink_id, _criticality_q in connection_timing.get(net_id, [])
        )

    def metrics() -> tuple[int, int, int]:
        wire = sum(hpwl(members, positions) for members in net_members.values())
        timing = sum(timing_cost(net_id, positions) for net_id in net_members)
        return wire, timing, wire_weight * wire + timing_weight * timing

    initial_wire, initial_timing, initial_objective = metrics()
    initial_connection_wire = sum(connection_wire_cost(net_id, positions) for net_id in net_members)
    accepted_total = 0
    rejected_conflicts = 0
    rejected_guard_candidates = 0
    rejected_wire_candidates = 0
    rejected_connection_wire_candidates = 0
    max_rejected_guard_overrun = 0
    pass_reports = []
    worker_pool = None
    worker_count = min(proposal_workers, len(units))
    for pass_index in range(passes):
        occupied = {loc: block_id for block_id, loc in positions.items()}
        def evaluate_unit(
            unit: tuple[int, ...],
            active_positions: dict[int, tuple[int, int, int, int]],
            active_occupied: dict[tuple[int, int, int, int], int],
        ) -> tuple[Any, int, int, int, int]:
            local_rejected_guard = 0
            local_rejected_wire = 0
            local_rejected_connection_wire = 0
            local_max_guard_overrun = 0
            members = [block_by_id[block_id] for block_id in unit]
            if any(block.get("fixed") for block in members):
                return None, 0, 0, 0, 0
            first = members[0]
            first_loc = active_positions[first["block_id"]]
            first_page = page_key(first_loc, page_width, page_height)
            candidate_pages = [
                (first_page[0], first_page[1] + dx, first_page[2] + dy)
                for dy in (-1, 0, 1)
                for dx in (-1, 0, 1)
            ]
            first_sites = []
            for key in candidate_pages:
                first_sites.extend(sites_by_page_type.get((key, first["logical_type"]), []))
            first_sites = sorted(
                set(first_sites),
                key=lambda loc: (
                    abs(loc[0] - first_loc[0]) + abs(loc[1] - first_loc[1]),
                    loc[3], loc[1], loc[0], loc[2],
                ),
            )[:candidate_limit]
            touched_nets = set().union(*(block_nets.get(block_id, set()) for block_id in unit))
            before = sum(net_objective(net_id, active_positions) for net_id in touched_nets)
            before_wire = (
                sum(hpwl(net_members[net_id], active_positions) for net_id in touched_nets)
                if max_wire_delta is not None or eager_disabled_guard_costs
                else 0
            )
            before_connection_wire = (
                sum(connection_wire_cost(net_id, active_positions) for net_id in touched_nets)
                if max_connection_wire_delta is not None or eager_disabled_guard_costs
                else 0
            )
            best = None
            first_macro = first.get("macro")
            for target_first in first_sites:
                if first_macro:
                    anchor = (
                        target_first[0] - first_macro["dx"],
                        target_first[1] - first_macro["dy"],
                        target_first[2] - first_macro["dsubtile"],
                        target_first[3] - first_macro["dlayer"],
                    )
                else:
                    anchor = target_first
                trial: dict[int, tuple[int, int, int, int]] = {}
                valid = True
                for block in members:
                    macro = block.get("macro")
                    target = (
                        anchor[0] + (macro["dx"] if macro else 0),
                        anchor[1] + (macro["dy"] if macro else 0),
                        anchor[2] + (macro["dsubtile"] if macro else 0),
                        anchor[3] + (macro["dlayer"] if macro else 0),
                    )
                    site = site_by_loc.get(target)
                    owner = active_occupied.get(target)
                    if (
                        site is None
                        or site["physical_type"] != block["logical_type"]
                        or (owner is not None and owner not in unit)
                        or target in trial.values()
                        or not in_region(block, target)
                        or not matches_fixed(block, target)
                    ):
                        valid = False
                        break
                    trial[block["block_id"]] = target
                if not valid or all(
                    trial[block_id] == active_positions[block_id] for block_id in unit
                ):
                    continue
                candidate_positions = dict(active_positions)
                candidate_positions.update(trial)
                guard_overrun = max(
                    (
                        manhattan(source_id, sink_id, candidate_positions)
                        - initial_distance
                        - critical_distance_slack
                        for net_id in touched_nets
                        for source_id, sink_id, _criticality_q, initial_distance
                        in guarded_connections.get(net_id, [])
                    ),
                    default=0,
                )
                if guard_overrun > 0:
                    local_rejected_guard += 1
                    local_max_guard_overrun = max(local_max_guard_overrun, guard_overrun)
                    continue
                if max_wire_delta is not None:
                    after_wire = sum(
                        hpwl(net_members[net_id], candidate_positions) for net_id in touched_nets
                    )
                    if after_wire - before_wire > max_wire_delta:
                        local_rejected_wire += 1
                        continue
                if max_connection_wire_delta is not None:
                    after_connection_wire = sum(
                        connection_wire_cost(net_id, candidate_positions)
                        for net_id in touched_nets
                    )
                    if (
                        after_connection_wire - before_connection_wire
                        > max_connection_wire_delta
                    ):
                        local_rejected_connection_wire += 1
                        continue
                after = sum(net_objective(net_id, candidate_positions) for net_id in touched_nets)
                delta = after - before
                score = (delta, tuple(trial[block_id] for block_id in unit))
                if delta < 0 and (best is None or score < best[0]):
                    best = (score, trial)
            proposal = None
            if best is not None:
                delta = best[0][0]
                trial = best[1]
                proposal = {
                    "unit": unit,
                    "delta": delta,
                    "trial": trial,
                    "nets": touched_nets,
                    "sites": set(active_positions[block_id] for block_id in unit)
                    | set(trial.values()),
                    "page_color": (first_page[1] & 1, first_page[2] & 1),
                }
            return (
                proposal,
                local_rejected_guard,
                local_max_guard_overrun,
                local_rejected_wire,
                local_rejected_connection_wire,
            )

        if proposal_workers == 1:
            evaluated = [evaluate_unit(unit, positions, occupied) for unit in units]
        else:
            if "fork" not in multiprocessing.get_all_start_methods():
                raise ContractError("parallel proposal evaluation requires the Linux fork start method")
            global _FORK_PROPOSAL_EVALUATOR
            if worker_pool is None:
                _FORK_PROPOSAL_EVALUATOR = evaluate_unit
                worker_pool = multiprocessing.get_context("fork").Pool(worker_count)
            chunks = [list(units[index::worker_count]) for index in range(worker_count)]
            try:
                chunk_results = worker_pool.map(
                    _evaluate_fork_chunk,
                    [(chunk, positions, occupied) for chunk in chunks],
                    1,
                )
            except BaseException:
                worker_pool.terminate()
                worker_pool.join()
                worker_pool = None
                _FORK_PROPOSAL_EVALUATOR = None
                raise
            evaluated = [result for chunk_result in chunk_results for result in chunk_result]

        proposals = []
        for (
            proposal,
            local_rejected_guard,
            local_max_guard_overrun,
            local_rejected_wire,
            local_rejected_connection_wire,
        ) in evaluated:
            rejected_guard_candidates += local_rejected_guard
            max_rejected_guard_overrun = max(
                max_rejected_guard_overrun, local_max_guard_overrun
            )
            rejected_wire_candidates += local_rejected_wire
            rejected_connection_wire_candidates += local_rejected_connection_wire
            if proposal is not None:
                proposals.append(proposal)

        proposals.sort(key=lambda proposal: (proposal["delta"], proposal["page_color"], proposal["unit"]))
        reserved_sites: set[tuple[int, int, int, int]] = set()
        reserved_nets: set[int] = set()
        accepted = []
        for proposal in proposals:
            if proposal["sites"] & reserved_sites or proposal["nets"] & reserved_nets:
                rejected_conflicts += 1
                continue
            accepted.append(proposal)
            reserved_sites.update(proposal["sites"])
            reserved_nets.update(proposal["nets"])
        for proposal in accepted:
            positions.update(proposal["trial"])
        accepted_total += len(accepted)
        _wire, _timing, objective = metrics()
        pass_reports.append(
            {
                "pass": pass_index,
                "proposals": len(proposals),
                "accepted": len(accepted),
                "objective": objective,
            }
        )
        if not accepted:
            break

    if worker_pool is not None:
        worker_pool.close()
        worker_pool.join()
        _FORK_PROPOSAL_EVALUATOR = None

    write_place(output_place, header or manifest.get("placement_header", {}), blocks, positions)
    validation = validate_contract(contract, output_place)
    final_wire, final_timing, final_objective = metrics()
    final_connection_wire = sum(connection_wire_cost(net_id, positions) for net_id in net_members)
    guarded_final_deltas = [
        manhattan(source_id, sink_id, positions) - initial_distance
        for connections in guarded_connections.values()
        for source_id, sink_id, _criticality_q, initial_distance in connections
    ]
    report = {
        "schema": "TILEPLACE_PAGE_INCREMENTAL_CPU_V1",
        "status": "pass",
        "legal": validation["legal"],
        "input_place_sha256": sha256(input_place),
        "output_place_sha256": sha256(output_place),
        "blocks": len(blocks),
        "nets_with_multiple_blocks": len(net_members),
        "macro_units": len(macro_groups),
        "units": len(units),
        "page_width": page_width,
        "page_height": page_height,
        "pages": len({key for key, _physical_type in sites_by_page_type}),
        "page_colors": 4,
        "candidate_limit": candidate_limit,
        "proposal_workers": proposal_workers,
        "proposal_parallel_backend": "linux_fork_process_pool" if proposal_workers > 1 else "serial",
        "eager_disabled_guard_costs": eager_disabled_guard_costs,
        "wire_weight": wire_weight,
        "timing_weight": timing_weight,
        "timing_model": timing_model,
        "critical_distance_guard_q": critical_distance_guard_q,
        "critical_distance_slack": critical_distance_slack,
        "max_wire_delta": max_wire_delta,
        "max_connection_wire_delta": max_connection_wire_delta,
        "guarded_connections": len(guarded_final_deltas),
        "rejected_guard_candidates": rejected_guard_candidates,
        "rejected_wire_candidates": rejected_wire_candidates,
        "rejected_connection_wire_candidates": rejected_connection_wire_candidates,
        "max_rejected_guard_overrun": max_rejected_guard_overrun,
        "guarded_connections_increased": sum(delta > 0 for delta in guarded_final_deltas),
        "max_guarded_connection_delta": max(guarded_final_deltas, default=0),
        "timed_connections": timed_connections,
        "mapped_timed_connections": mapped_timed_connections,
        "timing_mapping_coverage": (
            mapped_timed_connections / timed_connections if timed_connections else None
        ),
        "initial_wire_hpwl": initial_wire,
        "final_wire_hpwl": final_wire,
        "initial_connection_wire": initial_connection_wire,
        "final_connection_wire": final_connection_wire,
        "initial_timing_hpwl_q": initial_timing,
        "final_timing_hpwl_q": final_timing,
        "initial_objective": initial_objective,
        "final_objective": final_objective,
        "accepted_moves": accepted_total,
        "rejected_conflicts": rejected_conflicts,
        "passes": pass_reports,
        "conflict_protocol": "snapshot proposals; disjoint old/new site write-set and touched-net set; deterministic delta/color/unit commit",
        "claim_boundary": "Internal HPWL is a research objective; VPR-native routed WL/CPD is required for QoR claims.",
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--input-place", type=Path, required=True)
    parser.add_argument("--output-place", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--page-width", type=int, default=4)
    parser.add_argument("--page-height", type=int, default=4)
    parser.add_argument("--passes", type=int, default=8)
    parser.add_argument("--candidate-limit", type=int, default=64)
    parser.add_argument("--proposal-workers", type=int, default=1)
    parser.add_argument("--eager-disabled-guard-costs", action="store_true")
    parser.add_argument("--wire-weight", type=int, default=256)
    parser.add_argument("--timing-weight", type=int, default=1)
    parser.add_argument(
        "--timing-model", choices=("net_hpwl", "connection_star"), default="net_hpwl"
    )
    parser.add_argument(
        "--critical-distance-guard-q",
        type=int,
        default=0,
        help="for mapped connections at or above this criticality, cap Manhattan distance relative to the input (0 disables)",
    )
    parser.add_argument(
        "--critical-distance-slack",
        type=int,
        default=0,
        help="allowed Manhattan-distance increase for guarded connections",
    )
    parser.add_argument(
        "--max-wire-delta",
        type=int,
        help="maximum touched-net HPWL increase allowed for each candidate transaction",
    )
    parser.add_argument(
        "--max-connection-wire-delta",
        type=int,
        help="maximum unweighted source/sink Manhattan increase allowed for each transaction",
    )
    args = parser.parse_args()
    try:
        if min(
            args.page_width,
            args.page_height,
            args.passes,
            args.candidate_limit,
            args.proposal_workers,
        ) <= 0:
            raise ContractError(
                "page dimensions, passes, candidate limit, and proposal workers must be positive"
            )
        if min(args.wire_weight, args.timing_weight, args.critical_distance_guard_q, args.critical_distance_slack) < 0:
            raise ContractError("weights and critical-distance guard parameters must be non-negative")
        report = optimize(
            args.contract.resolve(), args.input_place.resolve(), args.output_place.resolve(),
            args.page_width, args.page_height, args.passes, args.candidate_limit,
            args.wire_weight, args.timing_weight, args.timing_model,
            args.critical_distance_guard_q, args.critical_distance_slack,
            args.max_wire_delta,
            args.max_connection_wire_delta,
            args.proposal_workers,
            args.eager_disabled_guard_costs,
        )
        dump_json(args.report.resolve(), report)
        print(json.dumps(report, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"tileplace_research: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
