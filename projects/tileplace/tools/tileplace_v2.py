#!/usr/bin/env python3
"""Deterministic TilePlace V2 exchange/chain transaction engine.

This module deliberately does not call VPR.  It produces one color-phase batch
from an immutable placement snapshot; run_tileplace_v2.py owns routed-oracle
acceptance, rollback, and feedback refresh.
"""

from __future__ import annotations

import argparse
import json
from bisect import bisect_left
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable

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


Q20 = 1 << 20
PRESSURE_ONE = 1 << 16


@dataclass(frozen=True)
class V2Config:
    page_width: int = 2
    page_height: int = 2
    candidate_limit: int = 64
    chain_candidate_limit: int = 16
    timing_weight: int = 2
    routed_timing_weight: int = 0
    congestion_weight: int = 1
    critical_distance_guard_q: int = 60000
    critical_distance_slack: int = 0

    def validate(self) -> None:
        values = (
            self.page_width,
            self.page_height,
            self.candidate_limit,
            self.chain_candidate_limit,
            self.timing_weight,
        )
        if min(values) <= 0 or self.congestion_weight < 0 or self.routed_timing_weight < 0:
            raise ContractError("V2 dimensions, limits, and weights are invalid")
        if self.critical_distance_guard_q < 0 or self.critical_distance_slack < 0:
            raise ContractError("V2 guard parameters must be non-negative")


@dataclass
class Transaction:
    transaction_id: tuple[Any, ...]
    kind: str
    units: tuple[tuple[int, ...], ...]
    trial: dict[int, tuple[int, int, int, int]]
    touched_nets: frozenset[int]
    write_sites: frozenset[tuple[int, int, int, int]]
    score_q20: int
    wire_delta: int
    timing_delta: int
    routed_timing_delta: int
    congestion_delta: int

    def audit(self) -> dict[str, Any]:
        return {
            "id": repr(self.transaction_id),
            "kind": self.kind,
            "units": [list(unit) for unit in self.units],
            "trial": {str(key): list(value) for key, value in sorted(self.trial.items())},
            "touched_nets": sorted(self.touched_nets),
            "write_sites": [list(value) for value in sorted(self.write_sites)],
            "score_q20": self.score_q20,
            "wire_delta": self.wire_delta,
            "timing_delta": self.timing_delta,
            "routed_timing_delta": self.routed_timing_delta,
            "congestion_delta": self.congestion_delta,
        }


def _edge_key(x0: int, y0: int, x1: int, y1: int) -> tuple[int, int, int, int]:
    return (x0, y0, x1, y1) if (x0, y0) <= (x1, y1) else (x1, y1, x0, y0)


def load_feedback(path: Path | None) -> dict[tuple[int, int, int, int], int]:
    if path is None:
        return {}
    payload = json.loads(path.read_text())
    if payload.get("schema") != "TILEPLACE_ROUTE_FEEDBACK_V1":
        raise ContractError("unsupported TilePlace route-feedback schema")
    result: dict[tuple[int, int, int, int], int] = {}
    for row in payload.get("edges", []):
        key = _edge_key(int(row["x0"]), int(row["y0"]), int(row["x1"]), int(row["y1"]))
        pressure = int(row["pressure_q16"])
        if pressure < 0 or key in result:
            raise ContractError("invalid or duplicate route-feedback edge")
        result[key] = pressure
    return result


def load_timing_feedback(
    payload: dict[str, Any] | None,
) -> tuple[dict[tuple[int, int], int], set[int]]:
    if payload is None:
        return {}, set()
    if payload.get("schema") != "TILEPLACE_TIMING_FEEDBACK_V1":
        raise ContractError("unsupported TilePlace timing-feedback schema")
    edges: dict[tuple[int, int], int] = {}
    for row in payload.get("edges", []):
        key = tuple(sorted((int(row["source_block_id"]), int(row["sink_block_id"]))))
        weight = int(row["weight_q16"])
        if key[0] == key[1] or weight <= 0 or key in edges:
            raise ContractError("invalid or duplicate timing-feedback edge")
        edges[key] = weight
    focus = {int(value) for value in payload.get("focus_blocks", [])}
    if not edges or not focus:
        raise ContractError("timing feedback is empty")
    return edges, focus


class TilePlaceV2Engine:
    def __init__(
        self,
        contract: Path,
        input_place: Path,
        config: V2Config,
        pressure_q16: dict[tuple[int, int, int, int], int] | None = None,
        timing_feedback: tuple[dict[tuple[int, int], int], set[int]] | None = None,
    ) -> None:
        config.validate()
        self.contract = contract.resolve()
        self.input_place = input_place.resolve()
        self.config = config
        self.pressure_q16 = pressure_q16 or {}
        self.path_edges_q16, self.focus_blocks = timing_feedback or ({}, set())
        self.manifest, self.blocks, self.sites, self.nets = load_contract(self.contract)
        validate_contract(self.contract, self.input_place)
        self.header, rows = parse_place(self.input_place)
        row_by_name = {row["name"]: row for row in rows}
        self.block_by_id = {int(block["block_id"]): block for block in self.blocks}
        self.positions = {
            block_id: location(row_by_name[block["name"]])
            for block_id, block in self.block_by_id.items()
        }
        self.initial_positions = dict(self.positions)
        self.site_by_loc = {location(site): site for site in self.sites}
        self.sites_by_page_type: dict[
            tuple[tuple[int, int, int], str], list[tuple[int, int, int, int]]
        ] = defaultdict(list)
        for site in self.sites:
            loc = location(site)
            self.sites_by_page_type[(self.page_key(loc), site["physical_type"])].append(loc)
        for values in self.sites_by_page_type.values():
            values.sort(key=lambda loc: (loc[3], loc[1], loc[0], loc[2]))

        macro_groups: dict[str, list[int]] = defaultdict(list)
        independent: list[int] = []
        for block in self.blocks:
            block_id = int(block["block_id"])
            if block.get("macro"):
                macro_groups[str(block["macro"]["id"])].append(block_id)
            else:
                independent.append(block_id)
        self.units = [tuple(sorted(value)) for _key, value in sorted(macro_groups.items())]
        self.units.extend((block_id,) for block_id in sorted(independent))
        self.units.sort(key=lambda unit: (unit[0], len(unit), unit))
        self.unit_by_block = {block_id: unit for unit in self.units for block_id in unit}
        self.fixed_units = {
            unit for unit in self.units if any(self.block_by_id[block_id].get("fixed") for block_id in unit)
        }

        self.net_members: dict[int, list[int]] = {}
        self.connections: dict[int, list[tuple[int, int, int]]] = defaultdict(list)
        self.block_nets: dict[int, set[int]] = defaultdict(set)
        for net in self.nets:
            members = sorted(
                {int(pin["block_id"]) for pin in net.get("pins", []) if int(pin["block_id"]) in self.block_by_id}
            )
            if len(members) < 2:
                continue
            net_id = int(net["net_id"])
            self.net_members[net_id] = members
            for block_id in members:
                self.block_nets[block_id].add(net_id)
            for connection in net.get("connections", []):
                if "source_block_id" in connection and "sink_block_id" in connection:
                    self.connections[net_id].append(
                        (
                            int(connection["source_block_id"]),
                            int(connection["sink_block_id"]),
                            max(0, int(connection.get("criticality_q", 0))),
                        )
                    )
        if not any(self.connections.values()):
            raise ContractError("TilePlace V2 requires mapped connection endpoints")
        self._net_cost_cache: dict[int, tuple[int, int, int]] = {}
        self.guarded: list[tuple[int, int, int, int]] = []
        if config.critical_distance_guard_q > 0:
            for connections in self.connections.values():
                for source, sink, criticality in connections:
                    if criticality >= config.critical_distance_guard_q:
                        self.guarded.append(
                            (source, sink, criticality, self.manhattan(source, sink, self.initial_positions))
                        )

    def page_key(self, loc: tuple[int, int, int, int]) -> tuple[int, int, int]:
        return (
            loc[3],
            loc[0] // self.config.page_width,
            loc[1] // self.config.page_height,
        )

    @staticmethod
    def hpwl(members: Iterable[int], positions: dict[int, tuple[int, int, int, int]]) -> int:
        locs = [positions[value] for value in members]
        if len(locs) < 2:
            return 0
        return max(value[0] for value in locs) - min(value[0] for value in locs) + max(
            value[1] for value in locs
        ) - min(value[1] for value in locs)

    @staticmethod
    def manhattan(
        source: int,
        sink: int,
        positions: dict[int, tuple[int, int, int, int]],
    ) -> int:
        a, b = positions[source], positions[sink]
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    @property
    def pressure_q16(self):
        return self._pressure_q16

    @pressure_q16.setter
    def pressure_q16(self, values):
        # Feedback is one immutable snapshot. Replacing it rebuilds the indexes
        # and invalidates net costs, including on accepted oracle refreshes.
        pressure_snapshot = MappingProxyType(dict(values))
        horizontal, vertical = defaultdict(list), defaultdict(list)
        for (x0, y0, x1, y1), weight in pressure_snapshot.items():
            if y0 == y1 and x1 == x0 + 1:
                horizontal[y0].append((x0, weight))
            elif x0 == x1 and y1 == y0 + 1:
                vertical[x0].append((y0, weight))

        def prefixes(lines):
            result = {}
            for line, entries in lines.items():
                entries.sort()
                coordinates, sums = [], [0]
                for coordinate, weight in entries:
                    coordinates.append(coordinate)
                    sums.append(sums[-1] + weight)
                result[line] = (coordinates, sums)
            return result

        horizontal_prefix = prefixes(horizontal)
        vertical_prefix = prefixes(vertical)
        self._pressure_q16 = pressure_snapshot
        self._horizontal_pressure = horizontal_prefix
        self._vertical_pressure = vertical_prefix
        if hasattr(self, "_net_cost_cache"):
            self._net_cost_cache.clear()

    @staticmethod
    def _segment_pressure(lines, line, start, end):
        if line not in lines or start == end:
            return 0
        coordinates, sums = lines[line]
        low, high = sorted((start, end))
        return sums[bisect_left(coordinates, high)] - sums[bisect_left(coordinates, low)]

    def _path_pressure(self, a: tuple[int, int], b: tuple[int, int], horizontal_first: bool) -> int:
        x, y = a
        target_x, target_y = b
        horizontal_y = y if horizontal_first else target_y
        vertical_x = target_x if horizontal_first else x
        return (
            (abs(target_x - x) + abs(target_y - y)) * PRESSURE_ONE
            + self._segment_pressure(self._horizontal_pressure, horizontal_y, x, target_x)
            + self._segment_pressure(self._vertical_pressure, vertical_x, y, target_y)
        )

    def _connection_congestion(
        self,
        source: int,
        sink: int,
        positions: dict[int, tuple[int, int, int, int]],
    ) -> int:
        a, b = positions[source], positions[sink]
        return min(
            self._path_pressure((a[0], a[1]), (b[0], b[1]), True),
            self._path_pressure((a[0], a[1]), (b[0], b[1]), False),
        )

    def _net_cost(
        self,
        net_id: int,
        positions: dict[int, tuple[int, int, int, int]],
    ) -> tuple[int, int, int]:
        cached = self._net_cost_cache.get(net_id)
        if cached is not None:
            return cached
        wire = self.hpwl(self.net_members[net_id], positions)
        timing = congestion = 0
        for source, sink, criticality in self.connections.get(net_id, []):
            timing += criticality * self.manhattan(source, sink, positions)
            congestion += self._connection_congestion(source, sink, positions)
        result = (wire, timing, congestion)
        self._net_cost_cache[net_id] = result
        return result

    def _cost_pair(
        self,
        touched_nets: Iterable[int],
        changed_blocks: frozenset[int],
        candidate: dict[int, tuple[int, int, int, int]],
    ) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
        before_wire = before_timing = before_congestion = 0
        after_wire = after_timing = after_congestion = 0
        for net_id in touched_nets:
            wire, timing, congestion = self._net_cost(net_id, self.positions)
            before_wire += wire
            before_timing += timing
            before_congestion += congestion
            after_wire += self.hpwl(self.net_members[net_id], candidate)
            after_timing += timing
            after_congestion += congestion
            for source, sink, criticality in self.connections.get(net_id, []):
                if source not in changed_blocks and sink not in changed_blocks:
                    continue
                after_timing += criticality * (
                    self.manhattan(source, sink, candidate)
                    - self.manhattan(source, sink, self.positions)
                )
                after_congestion += (
                    self._connection_congestion(source, sink, candidate)
                    - self._connection_congestion(source, sink, self.positions)
                )
        before_routed_timing = after_routed_timing = 0
        for (source, sink), weight in self.path_edges_q16.items():
            if source in changed_blocks or sink in changed_blocks:
                before_routed_timing += weight * self.manhattan(source, sink, self.positions)
                after_routed_timing += weight * self.manhattan(source, sink, candidate)
        return (
            (before_wire, before_timing, before_routed_timing, before_congestion),
            (after_wire, after_timing, after_routed_timing, after_congestion),
        )

    def update_timing_feedback(
        self,
        feedback: tuple[dict[tuple[int, int], int], set[int]],
    ) -> None:
        edges, focus = feedback
        unknown = (set(focus) | {value for edge in edges for value in edge}) - set(self.positions)
        if unknown or not edges or not focus:
            raise ContractError("timing feedback references unknown blocks or is empty")
        self.path_edges_q16 = dict(edges)
        self.focus_blocks = set(focus)

    def _candidate_roots(
        self,
        unit: tuple[int, ...],
        limit: int | None = None,
    ) -> list[tuple[int, int, int, int]]:
        root = unit[0]
        source = self.positions[root]
        page = self.page_key(source)
        result: list[tuple[int, int, int, int]] = []
        logical_type = self.block_by_id[root]["logical_type"]
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                result.extend(
                    self.sites_by_page_type.get(((page[0], page[1] + dx, page[2] + dy), logical_type), [])
                )
        maximum = self.config.candidate_limit if limit is None else limit
        return sorted(
            set(result),
            key=lambda loc: (
                abs(loc[0] - source[0]) + abs(loc[1] - source[1]),
                loc[3],
                loc[1],
                loc[0],
                loc[2],
            ),
        )[:maximum]

    def _translated(
        self,
        unit: tuple[int, ...],
        target_root: tuple[int, int, int, int],
    ) -> dict[int, tuple[int, int, int, int]]:
        root_loc = self.positions[unit[0]]
        delta = tuple(target_root[index] - root_loc[index] for index in range(4))
        return {
            block_id: tuple(self.positions[block_id][index] + delta[index] for index in range(4))
            for block_id in unit
        }

    def _shape_signature(self, unit: tuple[int, ...]) -> tuple[Any, ...]:
        root = self.positions[unit[0]]
        return tuple(
            sorted(
                (
                    self.block_by_id[block_id]["logical_type"],
                    tuple(self.positions[block_id][index] - root[index] for index in range(4)),
                )
                for block_id in unit
            )
        )

    def _valid_trial(
        self,
        trial: dict[int, tuple[int, int, int, int]],
        changed_blocks: frozenset[int],
        occupied: dict[tuple[int, int, int, int], int],
    ) -> bool:
        if len(set(trial.values())) != len(trial):
            return False
        for block_id, target in trial.items():
            block = self.block_by_id[block_id]
            site = self.site_by_loc.get(target)
            owner = occupied.get(target)
            if (
                site is None
                or site["physical_type"] != block["logical_type"]
                or (owner is not None and owner not in changed_blocks)
                or not in_region(block, target)
                or not matches_fixed(block, target)
            ):
                return False
        return True

    def _guard_ok(self, candidate: dict[int, tuple[int, int, int, int]]) -> bool:
        positions = dict(self.positions)
        positions.update(candidate)
        return all(
            self.manhattan(source, sink, positions)
            <= initial_distance + self.config.critical_distance_slack
            for source, sink, _criticality, initial_distance in self.guarded
            if source in candidate or sink in candidate
        )

    def _make_transaction(
        self,
        kind: str,
        units: tuple[tuple[int, ...], ...],
        trial: dict[int, tuple[int, int, int, int]],
    ) -> Transaction | None:
        if all(self.positions[block_id] == target for block_id, target in trial.items()):
            return None
        if not self._guard_ok(trial):
            return None
        changed_blocks = frozenset(trial)
        touched = frozenset().union(*(self.block_nets.get(block_id, set()) for block_id in changed_blocks))
        candidate = dict(self.positions)
        candidate.update(trial)
        before, after = self._cost_pair(touched, changed_blocks, candidate)
        deltas = tuple(after[index] - before[index] for index in range(4))
        normalized = tuple((deltas[index] * Q20) // max(1, before[index]) for index in range(4))
        score = (
            normalized[0]
            + self.config.timing_weight * normalized[1]
            + self.config.routed_timing_weight * normalized[2]
            + self.config.congestion_weight * normalized[3]
        )
        if score >= 0:
            return None
        sites = frozenset(
            [self.positions[block_id] for block_id in changed_blocks]
            + [trial[block_id] for block_id in changed_blocks]
        )
        identity = (
            kind,
            tuple(sorted(units)),
            tuple((block_id, trial[block_id]) for block_id in sorted(trial)),
        )
        return Transaction(identity, kind, tuple(sorted(units)), trial, touched, sites, score, *deltas)

    def _transactions_for_unit(
        self,
        unit: tuple[int, ...],
        occupied: dict[tuple[int, int, int, int], int],
    ) -> list[Transaction]:
        if unit in self.fixed_units:
            return []
        result: list[Transaction] = []
        for target_root in self._candidate_roots(unit):
            direct = self._translated(unit, target_root)
            owners = {
                self.unit_by_block[occupied[target]]
                for target in direct.values()
                if target in occupied and occupied[target] not in unit
            }
            if not owners:
                changed = frozenset(unit)
                if self._valid_trial(direct, changed, occupied):
                    transaction = self._make_transaction("move", (unit,), direct)
                    if transaction:
                        result.append(transaction)
                continue
            if len(owners) != 1:
                continue
            other = next(iter(owners))
            if other == unit or other in self.fixed_units:
                continue
            if len(unit) == len(other) and self._shape_signature(unit) == self._shape_signature(other):
                trial = self._translated(unit, self.positions[other[0]])
                trial.update(self._translated(other, self.positions[unit[0]]))
                changed = frozenset(unit + other)
                if self._valid_trial(trial, changed, occupied):
                    transaction = self._make_transaction(
                        "swap" if len(unit) == 1 else "macro_swap", (unit, other), trial
                    )
                    if transaction:
                        result.append(transaction)
            if len(unit) != 1 or len(other) != 1:
                continue
            for second_target in self._candidate_roots(other, self.config.chain_candidate_limit):
                if second_target == self.positions[other[0]]:
                    continue
                second_owner_block = occupied.get(second_target)
                if second_owner_block is None:
                    trial = {unit[0]: target_root, other[0]: second_target}
                    changed = frozenset(trial)
                    if self._valid_trial(trial, changed, occupied):
                        transaction = self._make_transaction("chain2", (unit, other), trial)
                        if transaction:
                            result.append(transaction)
                    continue
                third = self.unit_by_block[second_owner_block]
                if len(third) != 1 or third in (unit, other) or third in self.fixed_units:
                    continue
                trial = {
                    unit[0]: target_root,
                    other[0]: second_target,
                    third[0]: self.positions[unit[0]],
                }
                changed = frozenset(trial)
                if self._valid_trial(trial, changed, occupied):
                    transaction = self._make_transaction("chain3", (unit, other, third), trial)
                    if transaction:
                        result.append(transaction)
        return result

    def propose_color(
        self,
        color: int,
        forbidden_ids: set[tuple[Any, ...]] | None = None,
    ) -> tuple[list[Transaction], dict[str, Any]]:
        if not 0 <= color < 4:
            raise ContractError("color must be in [0, 3]")
        occupied = {loc: block_id for block_id, loc in self.positions.items()}
        color_units = [
            unit
            for unit in self.units
            if (not self.focus_blocks or any(block_id in self.focus_blocks for block_id in unit))
            if ((self.page_key(self.positions[unit[0]])[1] & 1) << 1)
            + (self.page_key(self.positions[unit[0]])[2] & 1)
            == color
        ]
        forbidden_ids = forbidden_ids or set()
        best_by_id: dict[tuple[Any, ...], Transaction] = {}
        kind_counts: dict[str, int] = defaultdict(int)
        for unit in color_units:
            candidates = [
                value
                for value in self._transactions_for_unit(unit, occupied)
                if value.transaction_id not in forbidden_ids
            ]
            if not candidates:
                continue
            best = min(candidates, key=lambda value: (value.score_q20, value.transaction_id))
            old = best_by_id.get(best.transaction_id)
            if old is None or (best.score_q20, best.transaction_id) < (old.score_q20, old.transaction_id):
                best_by_id[best.transaction_id] = best
        proposals = sorted(best_by_id.values(), key=lambda value: (value.score_q20, value.transaction_id))
        reserved_sites: set[tuple[int, int, int, int]] = set()
        reserved_nets: set[int] = set()
        reserved_units: set[tuple[int, ...]] = set()
        accepted: list[Transaction] = []
        rejected_conflicts = 0
        for transaction in proposals:
            if (
                transaction.write_sites & reserved_sites
                or transaction.touched_nets & reserved_nets
                or any(unit in reserved_units for unit in transaction.units)
            ):
                rejected_conflicts += 1
                continue
            accepted.append(transaction)
            reserved_sites.update(transaction.write_sites)
            reserved_nets.update(transaction.touched_nets)
            reserved_units.update(transaction.units)
            kind_counts[transaction.kind] += 1
        return accepted, {
            "color": color,
            "eligible_units": len(color_units),
            "proposals": len(proposals),
            "accepted": len(accepted),
            "rejected_conflicts": rejected_conflicts,
            "forbidden_transactions": len(forbidden_ids),
            "accepted_kinds": dict(sorted(kind_counts.items())),
        }

    def apply(self, transactions: Iterable[Transaction]) -> None:
        for transaction in transactions:
            self.positions.update(transaction.trial)
        self._net_cost_cache.clear()

    def snapshot(self) -> dict[int, tuple[int, int, int, int]]:
        return dict(self.positions)

    def restore(self, positions: dict[int, tuple[int, int, int, int]]) -> None:
        if set(positions) != set(self.positions):
            raise ContractError("V2 snapshot block set differs")
        self.positions = dict(positions)
        self._net_cost_cache.clear()

    def write_place(self, path: Path) -> None:
        lines: list[str] = []
        header = self.header or self.manifest.get("placement_header", {})
        if header.get("netlist"):
            lines.append(header["netlist"])
        if header.get("array_size"):
            lines.append(header["array_size"])
        lines.extend(["", "#block name\tx\ty\tsubblk\tlayer\tblock number"])
        for block in sorted(self.blocks, key=lambda value: (value["block_id"], value["name"])):
            x, y, subtile, layer = self.positions[int(block["block_id"])]
            lines.append(f"{block['name']}\t{x}\t{y}\t{subtile}\t{layer}\t#{block['block_id']}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n")
        validate_contract(self.contract, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--input-place", type=Path, required=True)
    parser.add_argument("--output-place", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--feedback", type=Path)
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--timing-weight", type=int, choices=(2, 4), default=2)
    parser.add_argument("--congestion-weight", type=int, choices=(0, 1), default=1)
    args = parser.parse_args()
    try:
        if args.epochs <= 0:
            raise ContractError("epochs must be positive")
        config = V2Config(timing_weight=args.timing_weight, congestion_weight=args.congestion_weight)
        engine = TilePlaceV2Engine(
            args.contract, args.input_place, config, load_feedback(args.feedback)
        )
        phases = []
        transactions = []
        for epoch in range(args.epochs):
            epoch_accepted = 0
            for color in range(4):
                batch, audit = engine.propose_color(color)
                audit["epoch"] = epoch
                phases.append(audit)
                engine.apply(batch)
                transactions.extend(value.audit() for value in batch)
                epoch_accepted += len(batch)
            if epoch_accepted == 0:
                break
        engine.write_place(args.output_place.resolve())
        report = {
            "schema": "TILEPLACE_V2_OFFLINE_REPORT_V1",
            "status": "pass",
            "config": config.__dict__,
            "input_place_sha256": sha256(args.input_place.resolve()),
            "output_place_sha256": sha256(args.output_place.resolve()),
            "phases": phases,
            "transactions": transactions,
            "accepted_transactions": len(transactions),
        }
        dump_json(args.report.resolve(), report)
        print(json.dumps(report, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"tileplace_v2: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
