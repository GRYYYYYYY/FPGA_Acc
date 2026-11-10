#!/usr/bin/env python3
"""TilePlace VPR contract packer, deterministic CPU legalizer, and validator.

The contract is intentionally line-oriented.  Large block/site/net collections
remain streamable JSONL files while the compact manifest records provenance and
SHA-256 hashes.  The CPU legalizer is a correctness reference, not a QoR claim.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "TILEPLACE_VPR_CONTRACT_V1"
PLACE_SCHEMA = "TILEPLACE_CPU_GOLDEN_V1"
INSTANCE_RE = re.compile(r"^(.*)\[\d+\]$")
PIN_CAPACITY_RE = re.compile(r"^([^.[\]]+)\[(\d+)\]\.")
MACRO_HEADER_RE = re.compile(r"^Macro_Id:\s*(\d+),\s*Num_Blocks:\s*(\d+)\s*$")
MACRO_MEMBER_RE = re.compile(
    r"^Block_Id:\s*(\d+)\s+\((.*)\),\s*x_offset:\s*(-?\d+),\s*"
    r"y_offset:\s*(-?\d+),\s*z_offset:\s*(-?\d+)\s*$"
)


class ContractError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dump_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> tuple[int, str]:
    count = 0
    digest = hashlib.sha256()
    with path.open("wb") as stream:
        for row in rows:
            encoded = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
            stream.write(encoded)
            digest.update(encoded)
            count += 1
    return count, digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open() as stream:
        return [json.loads(line) for line in stream if line.strip()]


def parse_place(path: Path) -> tuple[dict[str, str], list[dict[str, Any]]]:
    header: dict[str, str] = {}
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line_number, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("Netlist_File:"):
            header["netlist"] = line
            continue
        if line.startswith("Array size:"):
            header["array_size"] = line
            continue
        fields = line.split()
        if len(fields) < 5:
            raise ContractError(f"{path}:{line_number}: malformed placement row")
        name = fields[0]
        if name in seen:
            raise ContractError(f"{path}:{line_number}: duplicate block {name!r}")
        try:
            x, y, subtile, layer = map(int, fields[1:5])
        except ValueError as error:
            raise ContractError(f"{path}:{line_number}: non-integer coordinate") from error
        block_number = None
        for field in fields[5:]:
            if field.startswith("#") and field[1:].isdigit():
                block_number = int(field[1:])
                break
        rows.append(
            {
                "name": name,
                "x": x,
                "y": y,
                "subtile": subtile,
                "layer": layer,
                "block_number": block_number,
            }
        )
        seen.add(name)
    if not rows:
        raise ContractError(f"{path}: no placement rows")
    return header, rows


def logical_type(instance: str) -> str:
    match = INSTANCE_RE.match(instance)
    return match.group(1) if match else instance


def load_constraints(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"fixed": [], "fixed_locations": {}, "regions": {}, "macros": []}
    value = json.loads(path.read_text())
    for key, expected in (
        ("fixed", list),
        ("fixed_locations", dict),
        ("regions", dict),
        ("macros", list),
    ):
        value.setdefault(key, expected())
        if not isinstance(value[key], expected):
            raise ContractError(f"constraints field {key!r} has the wrong type")
    return value


def packed_atom_clusters(path: Path) -> dict[str, str]:
    """Return the packed cluster containing every primitive atom.

    VPR applies XML constraints to atom blocks and intersects the constraints of
    all atoms packed into a cluster.  A primitive atom is represented by a
    non-open leaf ``block`` in the packed netlist.
    """
    block_stack: list[dict[str, Any]] = []
    atoms: dict[str, str] = {}
    for event, element in ET.iterparse(path, events=("start", "end")):
        if event == "start":
            if element.tag == "block":
                name = element.attrib.get("name", "")
                if block_stack and name != "open":
                    block_stack[-1]["real_child"] = True
                if not block_stack:
                    cluster = ""
                elif len(block_stack) == 1:
                    cluster = name
                else:
                    cluster = block_stack[1]["name"]
                block_stack.append({"name": name, "cluster": cluster, "real_child": False})
            continue

        if element.tag == "block":
            frame = block_stack.pop()
            name = frame["name"]
            if name != "open" and not frame["real_child"] and len(block_stack) >= 2:
                previous = atoms.setdefault(name, frame["cluster"])
                if previous != frame["cluster"]:
                    raise ContractError(
                        f"packed atom {name!r} appears in multiple clusters: "
                        f"{previous!r}, {frame['cluster']!r}"
                    )
            element.clear()
    if not atoms:
        raise ContractError(f"{path}: no primitive atoms in packed netlist")
    return atoms


def intersect_regions(left: list[dict[str, int]], right: list[dict[str, int]]) -> list[dict[str, int]]:
    intersections: list[dict[str, int]] = []
    for first in left:
        for second in right:
            first_subtile = first["subtile"]
            second_subtile = second["subtile"]
            if first_subtile != -1 and second_subtile != -1 and first_subtile != second_subtile:
                continue
            region = {
                "xmin": max(first["xmin"], second["xmin"]),
                "ymin": max(first["ymin"], second["ymin"]),
                "xmax": min(first["xmax"], second["xmax"]),
                "ymax": min(first["ymax"], second["ymax"]),
                "layer_low": max(first["layer_low"], second["layer_low"]),
                "layer_high": min(first["layer_high"], second["layer_high"]),
                "subtile": first_subtile if first_subtile != -1 else second_subtile,
            }
            if (
                region["xmin"] <= region["xmax"]
                and region["ymin"] <= region["ymax"]
                and region["layer_low"] <= region["layer_high"]
            ):
                intersections.append(region)
    unique = {tuple(sorted(region.items())): region for region in intersections}
    return [unique[key] for key in sorted(unique)]


def point_fixed_location(regions: list[dict[str, int]]) -> dict[str, int | None] | None:
    """Return VPR AP-style fixed dimensions for a single coordinate.

    VPR analytical placement allows the subtile to remain unspecified while
    fixing x, y, and layer.  Multiple regions only qualify when they describe
    the same fixed coordinate.
    """
    if not regions or any(
        region["xmin"] != region["xmax"]
        or region["ymin"] != region["ymax"]
        or region["layer_low"] != region["layer_high"]
        for region in regions
    ):
        return None
    points = {
        (region["xmin"], region["ymin"], region["layer_low"])
        for region in regions
    }
    if len(points) != 1:
        return None
    x, y, layer = next(iter(points))
    specified_subtiles = {region["subtile"] for region in regions if region["subtile"] != -1}
    subtile = (
        next(iter(specified_subtiles))
        if all(region["subtile"] != -1 for region in regions) and len(specified_subtiles) == 1
        else None
    )
    return {"x": x, "y": y, "subtile": subtile, "layer": layer}


def parse_vpr_constraints(path: Path, packed_netlist: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Import VPR placement constraints using VPR's atom/partition semantics."""
    root = ET.parse(path).getroot()
    if root.tag != "vpr_constraints":
        raise ContractError(f"{path}: root element is not vpr_constraints")
    partition_list = root.find("partition_list")
    if partition_list is None:
        raise ContractError(f"{path}: no placement partition_list")

    atom_clusters = packed_atom_clusters(packed_netlist)
    atom_partition: dict[str, str] = {}
    partitions: dict[str, list[dict[str, int]]] = {}
    pattern_count = 0
    for partition in partition_list.findall("partition"):
        partition_name = partition.attrib.get("name", "")
        if not partition_name or partition_name in partitions:
            raise ContractError(f"{path}: missing or duplicate partition name {partition_name!r}")
        regions: list[dict[str, int]] = []
        for element in partition:
            if element.tag == "add_atom":
                pattern_count += 1
                pattern = element.attrib.get("name_pattern")
                if not pattern:
                    raise ContractError(f"{path}: partition {partition_name!r} has an empty atom pattern")
                if pattern in atom_clusters:
                    matches = [pattern]
                else:
                    try:
                        expression = re.compile(pattern)
                    except re.error as error:
                        raise ContractError(f"{path}: invalid atom regex {pattern!r}: {error}") from error
                    matches = [name for name in atom_clusters if expression.search(name)]
                if not matches:
                    raise ContractError(f"{path}: atom pattern {pattern!r} matches no packed atom")
                for atom in matches:
                    # This deliberately mirrors UserPlaceConstraints: the last
                    # partition assignment wins for an atom.
                    atom_partition[atom] = partition_name
            elif element.tag == "add_region":
                try:
                    region = {
                        "xmin": int(element.attrib["x_low"]),
                        "ymin": int(element.attrib["y_low"]),
                        "xmax": int(element.attrib["x_high"]),
                        "ymax": int(element.attrib["y_high"]),
                        "layer_low": int(element.attrib.get("layer_low", 0)),
                        "layer_high": int(element.attrib.get("layer_high", 0)),
                        "subtile": int(element.attrib.get("subtile", -1)),
                    }
                except (KeyError, ValueError) as error:
                    raise ContractError(
                        f"{path}: malformed region in partition {partition_name!r}"
                    ) from error
                if (
                    region["xmin"] > region["xmax"]
                    or region["ymin"] > region["ymax"]
                    or region["layer_low"] > region["layer_high"]
                ):
                    raise ContractError(f"{path}: empty region in partition {partition_name!r}")
                regions.append(region)
        if not regions:
            raise ContractError(f"{path}: partition {partition_name!r} has no region")
        partitions[partition_name] = regions

    cluster_partitions: dict[str, set[str]] = defaultdict(set)
    for atom, partition_name in atom_partition.items():
        cluster_partitions[atom_clusters[atom]].add(partition_name)
    regions_by_cluster: dict[str, list[dict[str, int]]] = {}
    fixed_locations: dict[str, dict[str, int | None]] = {}
    for cluster, partition_names in sorted(cluster_partitions.items()):
        cluster_regions: list[dict[str, int]] | None = None
        for partition_name in sorted(partition_names):
            cluster_regions = (
                partitions[partition_name]
                if cluster_regions is None
                else intersect_regions(cluster_regions, partitions[partition_name])
            )
        if not cluster_regions:
            raise ContractError(f"{path}: cluster {cluster!r} has incompatible atom constraints")
        regions_by_cluster[cluster] = cluster_regions
        fixed_location = point_fixed_location(cluster_regions)
        if fixed_location is not None:
            fixed_locations[cluster] = fixed_location

    constraints = {
        "fixed": [],
        "fixed_locations": fixed_locations,
        "regions": regions_by_cluster,
        "macros": [],
    }
    summary = {
        "source": "vpr_constraints_xml",
        "partitions": len(partitions),
        "atom_patterns": pattern_count,
        "matched_atoms": len(atom_partition),
        "constrained_clusters": len(regions_by_cluster),
        "coordinate_fixed_clusters": len(fixed_locations),
    }
    return constraints, summary


def parse_vpr_place_macros(
    path: Path, placements: dict[str, dict[str, Any]]
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Parse the exact placement macros emitted by this VPR revision.

    VPR derives these macros from architecture-level directs and clustered-netlist
    connectivity.  Consuming its echo avoids reimplementing physical-pin mapping
    and macro-combination semantics in the interchange packer.
    """
    lines = path.read_text().splitlines()
    try:
        declared = int(next(line for line in lines if line.startswith("Num_Macros:")).split(":", 1)[1])
    except (StopIteration, ValueError) as error:
        raise ContractError(f"{path}: missing or malformed Num_Macros") from error

    by_name: dict[str, dict[str, Any]] = {}
    parsed_ids: list[int] = []
    index = 0
    while index < len(lines):
        header = MACRO_HEADER_RE.match(lines[index].strip())
        if not header:
            index += 1
            continue
        macro_number, member_count = map(int, header.groups())
        parsed_ids.append(macro_number)
        members: list[tuple[int, str, int, int, int]] = []
        index += 1
        while index < len(lines) and len(members) < member_count:
            member = MACRO_MEMBER_RE.match(lines[index].strip())
            if member:
                block_id, name, dx, dy, dsubtile = member.groups()
                members.append((int(block_id), name, int(dx), int(dy), int(dsubtile)))
            elif MACRO_HEADER_RE.match(lines[index].strip()):
                break
            index += 1
        if len(members) != member_count:
            raise ContractError(
                f"{path}: macro {macro_number} declares {member_count} members but has {len(members)}"
            )
        if member_count < 2:
            raise ContractError(f"{path}: VPR macro {macro_number} has fewer than two members")
        macro_id = f"vpr_direct:{macro_number}"
        for block_id, name, dx, dy, dsubtile in members:
            placement = placements.get(name)
            if placement is None:
                raise ContractError(f"{path}: VPR macro {macro_number} references unknown block {name!r}")
            if placement["block_number"] != block_id:
                raise ContractError(
                    f"{path}: VPR macro {macro_number} block id/name mismatch for {name!r}"
                )
            if name in by_name:
                raise ContractError(f"{path}: block {name!r} belongs to multiple VPR macros")
            by_name[name] = {
                "id": macro_id,
                "dx": dx,
                "dy": dy,
                "dsubtile": dsubtile,
                "dlayer": 0,
                "source": "vpr_direct",
            }

    if len(parsed_ids) != declared:
        raise ContractError(f"{path}: declared {declared} VPR macros but parsed {len(parsed_ids)}")
    if parsed_ids != list(range(declared)):
        raise ContractError(f"{path}: VPR macro ids are not contiguous from zero")

    grouped: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for name, macro in by_name.items():
        grouped[macro["id"]].append((placements[name], macro))
    for macro_id, members in grouped.items():
        anchors = {
            (
                placement["x"] - macro["dx"],
                placement["y"] - macro["dy"],
                placement["subtile"] - macro["dsubtile"],
                placement["layer"] - macro["dlayer"],
            )
            for placement, macro in members
        }
        if len(anchors) != 1:
            raise ContractError(f"{path}: reference placement violates VPR macro {macro_id}")
    return by_name, {
        "source": "vpr_place_macros_echo",
        "macro_count": declared,
        "member_count": len(by_name),
    }


def block_pin_tokens(block: ET.Element) -> list[dict[str, str]]:
    pins: dict[tuple[str, str, str], dict[str, str]] = {}

    def walk(element: ET.Element, role: str | None, path: str) -> None:
        next_role = role
        if element.tag == "inputs":
            next_role = "sink"
        elif element.tag == "outputs":
            next_role = "source"
        elif element.tag == "clocks":
            next_role = "clock"
        next_path = path
        if element.tag == "port":
            next_path = f"{path}/{next_role}:{element.attrib.get('name', '')}"
            for token in (element.text or "").split():
                if token == "open" or "->" in token:
                    continue
                key = (token, next_role or "unknown", next_path)
                pins[key] = {"net": token, "role": key[1], "path": next_path}
        for child in element:
            walk(child, next_role, next_path)

    walk(block, None, block.attrib.get("instance", ""))
    return [pins[key] for key in sorted(pins)]


def parse_packed_netlist(
    path: Path,
    placements: dict[str, dict[str, Any]],
    constraints: dict[str, Any],
    native_macro_by_block: dict[str, dict[str, Any]],
) -> tuple[dict[str, str], list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    fixed = set(constraints["fixed"])
    fixed_locations = constraints.get("fixed_locations", {})
    regions = constraints["regions"]
    macro_by_block = dict(native_macro_by_block)
    for macro in constraints["macros"]:
        macro_id = str(macro.get("id", ""))
        members = macro.get("members", [])
        if not macro_id or not members:
            raise ContractError("every macro needs a non-empty id and members")
        for member in members:
            name = member.get("block")
            if not name or name in macro_by_block:
                raise ContractError(f"duplicate or missing macro member {name!r}")
            macro_by_block[name] = {
                "id": f"external:{macro_id}",
                "dx": int(member.get("dx", 0)),
                "dy": int(member.get("dy", 0)),
                "dsubtile": int(member.get("dsubtile", 0)),
                "dlayer": int(member.get("dlayer", 0)),
                "source": "external_constraint",
            }

    blocks: list[dict[str, Any]] = []
    net_pins: dict[str, list[dict[str, Any]]] = defaultdict(list)
    root_attributes: dict[str, str] = {}
    stack: list[ET.Element] = []
    for event, element in ET.iterparse(path, events=("start", "end")):
        if event == "start":
            stack.append(element)
            if len(stack) == 1:
                root_attributes = dict(element.attrib)
            continue
        if element.tag == "block" and len(stack) == 2:
            name = element.attrib.get("name", "")
            if name not in placements:
                raise ContractError(f"packed block {name!r} is absent from the placement")
            initial = {key: placements[name][key] for key in ("x", "y", "subtile", "layer")}
            region = regions.get(name)
            if region is not None:
                if not isinstance(region, list):
                    raise ContractError(f"region for {name!r} must be a list")
                if region and all(isinstance(value, int) for value in region):
                    if len(region) not in (4, 5):
                        raise ContractError(f"region for {name!r} must have 4 or 5 integers")
                    region = [int(value) for value in region]
                elif not all(isinstance(value, dict) for value in region):
                    raise ContractError(f"native regions for {name!r} must be dictionaries")
            fixed_location = fixed_locations.get(name)
            if fixed_location is not None:
                if not isinstance(fixed_location, dict):
                    raise ContractError(f"fixed location for {name!r} must be a dictionary")
                fixed_location = {
                    key: (None if fixed_location.get(key) is None else int(fixed_location[key]))
                    for key in ("x", "y", "subtile", "layer")
                }
            block_id = placements[name]["block_number"]
            if block_id is None:
                block_id = len(blocks)
            record = {
                "block_id": block_id,
                "name": name,
                "logical_type": logical_type(element.attrib.get("instance", "")),
                "mode": element.attrib.get("mode"),
                "initial": initial,
                "fixed": name in fixed or fixed_location is not None,
                "fixed_location": fixed_location,
                "region": region,
                "macro": macro_by_block.get(name),
            }
            blocks.append(record)
            for pin in block_pin_tokens(element):
                net_pins[pin.pop("net")].append({"block_id": block_id, **pin})
            element.clear()
        stack.pop()

    packed_names = {block["name"] for block in blocks}
    missing = sorted(set(placements) - packed_names)
    if missing:
        raise ContractError(f"placement has {len(missing)} blocks absent from packed netlist: {missing[:3]}")
    unknown_constraints = (
        fixed | set(fixed_locations) | set(regions) | set(macro_by_block)
    ) - packed_names
    if unknown_constraints:
        raise ContractError(f"constraints reference unknown blocks: {sorted(unknown_constraints)[:3]}")
    ids = [block["block_id"] for block in blocks]
    if len(ids) != len(set(ids)):
        raise ContractError("placement block numbers are not unique")
    blocks.sort(key=lambda block: (block["block_id"], block["name"]))
    return root_attributes, blocks, net_pins


def parse_rr_sites(
    path: Path, endpoint_node_ids: set[int] | None = None
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[int, dict[str, int]]]:
    block_types: dict[int, dict[str, Any]] = {}
    root_tiles: list[dict[str, int]] = []
    wanted = endpoint_node_ids or set()
    endpoint_locations: dict[int, dict[str, int]] = {}
    stack: list[ET.Element] = []
    record_containers = {
        "block_types", "grid", "rr_nodes", "rr_edges", "switches", "segments", "channels"
    }
    for event, element in ET.iterparse(path, events=("start", "end")):
        if event == "start":
            stack.append(element)
            continue
        parent = stack[-2] if len(stack) >= 2 else None
        if element.tag == "block_type":
            block_id = int(element.attrib["id"])
            name = element.attrib["name"]
            capacity = 1
            for pin in element.iter("pin"):
                match = PIN_CAPACITY_RE.match((pin.text or "").strip())
                if match and match.group(1) == name:
                    capacity = max(capacity, int(match.group(2)) + 1)
            block_types[block_id] = {
                "name": name,
                "width": int(element.attrib.get("width", 1)),
                "height": int(element.attrib.get("height", 1)),
                "capacity": capacity,
                "class_count": sum(1 for _pin_class in element.iter("pin_class")),
            }
        elif element.tag == "grid_loc":
            attrs = {key: int(value) for key, value in element.attrib.items()}
            if attrs.get("width_offset", 0) == 0 and attrs.get("height_offset", 0) == 0:
                root_tiles.append(attrs)
        elif element.tag == "node":
            node_id = int(element.attrib["id"])
            if node_id in wanted:
                loc = element.find("loc")
                if loc is None:
                    raise ContractError(f"RR node {node_id} has no loc")
                endpoint_locations[node_id] = {
                    "x": int(loc.attrib["xlow"]),
                    "y": int(loc.attrib["ylow"]),
                    "layer": int(loc.attrib.get("layer", 0)),
                    "ptc": int(loc.attrib["ptc"]),
                }
        endpoints_complete = bool(wanted) and len(endpoint_locations) == len(wanted)
        if parent is not None and parent.tag in record_containers:
            parent.remove(element)
            element.clear()
        stack.pop()
        if endpoints_complete and block_types and root_tiles:
            break

    sites: list[dict[str, Any]] = []
    for tile in sorted(root_tiles, key=lambda row: (row.get("layer", 0), row["y"], row["x"])):
        block_type = block_types[tile["block_type_id"]]
        if block_type["name"] == "EMPTY":
            continue
        for subtile in range(block_type["capacity"]):
            sites.append(
                {
                    "site_id": len(sites),
                    "physical_type": block_type["name"],
                    "x": tile["x"],
                    "y": tile["y"],
                    "subtile": subtile,
                    "layer": tile.get("layer", 0),
                    "width": block_type["width"],
                    "height": block_type["height"],
                }
            )
    if not sites:
        raise ContractError(f"{path}: no non-empty root sites")
    summary = {
        str(block_id): value for block_id, value in sorted(block_types.items())
    }
    missing_endpoints = wanted - set(endpoint_locations)
    if missing_endpoints:
        raise ContractError(f"RR graph is missing endpoint nodes: {sorted(missing_endpoints)[:3]}")
    return sites, summary, endpoint_locations


def parse_connections(
    path: Path | None, timing_path: Path | None
) -> tuple[dict[str, dict[str, Any]], dict[int, dict[str, int]]]:
    timing: dict[int, dict[str, int]] = {}
    if timing_path is not None:
        with timing_path.open(newline="") as stream:
            for row in csv.DictReader(stream):
                task_id = int(row["task_id"])
                record = {
                    key: int(row[key])
                    for key in ("criticality_q", "delay_ps", "slack_ps", "critical_path_delay_ps")
                }
                if row.get("timing_pin_mapped") not in (None, ""):
                    timing_pin_mapped = int(row["timing_pin_mapped"])
                    if timing_pin_mapped not in (0, 1):
                        raise ContractError(
                            f"timing task {task_id} has invalid timing_pin_mapped={timing_pin_mapped}"
                        )
                    record["timing_pin_mapped"] = timing_pin_mapped
                timing[task_id] = record
    by_name: dict[str, dict[str, Any]] = {}
    if path is None:
        return by_name, timing
    with path.open(newline="") as stream:
        for row in csv.DictReader(stream):
            task_id = int(row["id"])
            net_name = row["net"]
            record = by_name.setdefault(
                net_name,
                {"vpr_net_id": int(row["net_id"]), "connections": [], "criticality_q": 0},
            )
            if record["vpr_net_id"] != int(row["net_id"]):
                raise ContractError(f"net {net_name!r} has inconsistent VPR ids")
            connection = {
                "task_id": task_id,
                "source_rr_node": int(row["source"]),
                "sink_rr_node": int(row["sink"]),
            }
            if task_id in timing:
                connection.update(timing[task_id])
                record["criticality_q"] = max(record["criticality_q"], timing[task_id]["criticality_q"])
            record["connections"].append(connection)
    missing_timing = sorted(set(timing) - {c["task_id"] for value in by_name.values() for c in value["connections"]})
    if missing_timing:
        raise ContractError(f"timing file references unknown tasks: {missing_timing[:3]}")
    return by_name, timing


def make_nets(
    net_pins: dict[str, list[dict[str, Any]]], connections: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    names = sorted(set(net_pins) | set(connections), key=lambda name: (connections.get(name, {}).get("vpr_net_id", 1 << 62), name))
    rows = []
    for contract_net_id, name in enumerate(names):
        routed = connections.get(name, {})
        pins = sorted(net_pins.get(name, []), key=lambda pin: (pin["block_id"], pin["role"], pin["path"]))
        rows.append(
            {
                "net_id": contract_net_id,
                "vpr_net_id": routed.get("vpr_net_id"),
                "name": name,
                "criticality_q": routed.get("criticality_q", 0),
                "pins": pins,
                "connections": routed.get("connections", []),
            }
        )
    return rows


def annotate_connection_blocks(
    nets: list[dict[str, Any]],
    blocks: list[dict[str, Any]],
    endpoint_locations: dict[int, dict[str, int]],
    rr_block_types: dict[str, dict[str, Any]] | None = None,
) -> dict[str, int]:
    """Map routed connection endpoints back to clustered blocks.

    VPR's timing oracle is connection-specific.  RR terminal coordinates plus
    packed-net pin roles identify the source/sink clustered blocks without
    relying on route-file traversal order.
    """
    block_by_id = {block["block_id"]: block for block in blocks}
    block_type_by_name = {
        value["name"]: value for value in (rr_block_types or {}).values()
    }
    mapped_sources = 0
    mapped_sinks = 0
    timed_connections = 0
    timed_fully_mapped = 0
    atom_timing_pin_labeled = 0
    atom_timing_pin_mapped = 0
    for net in nets:
        source_ids = sorted({pin["block_id"] for pin in net["pins"] if pin["role"] == "source"})
        sink_ids = sorted({pin["block_id"] for pin in net["pins"] if pin["role"] in ("sink", "clock")})
        for connection in net["connections"]:
            if "criticality_q" in connection:
                timed_connections += 1
            if "timing_pin_mapped" in connection:
                atom_timing_pin_labeled += 1
                atom_timing_pin_mapped += connection["timing_pin_mapped"]
            if len(source_ids) == 1:
                connection["source_block_id"] = source_ids[0]
                mapped_sources += 1
            sink_rr = endpoint_locations.get(connection["sink_rr_node"])
            candidates = []
            if sink_rr is not None:
                for block_id in sink_ids:
                    block = block_by_id[block_id]
                    initial = block["initial"]
                    block_type = block_type_by_name.get(block["logical_type"], {})
                    width = block_type.get("width", 1)
                    height = block_type.get("height", 1)
                    if (
                        initial["x"] <= sink_rr["x"] < initial["x"] + width
                        and initial["y"] <= sink_rr["y"] < initial["y"] + height
                        and initial["layer"] == sink_rr["layer"]
                    ):
                        candidates.append(block_id)
            if len(candidates) > 1 and rr_block_types is not None:
                logical_type = block_by_id[candidates[0]]["logical_type"]
                block_type = block_type_by_name.get(logical_type)
                if block_type is not None:
                    capacity = block_type["capacity"]
                    class_count = block_type.get("class_count", 0)
                    if capacity > 0 and class_count > 0 and class_count % capacity == 0:
                        class_stride = class_count // capacity
                        rr_subtile = sink_rr["ptc"] // class_stride
                        subtile_candidates = [
                            block_id
                            for block_id in candidates
                            if block_by_id[block_id]["initial"]["subtile"] == rr_subtile
                        ]
                        if len(subtile_candidates) == 1:
                            candidates = subtile_candidates
            if len(candidates) == 1:
                connection["sink_block_id"] = candidates[0]
                mapped_sinks += 1
            if (
                "criticality_q" in connection
                and "source_block_id" in connection
                and "sink_block_id" in connection
            ):
                timed_fully_mapped += 1
    summary = {
        "connections": sum(len(net["connections"]) for net in nets),
        "mapped_sources": mapped_sources,
        "mapped_sinks": mapped_sinks,
        "timed_connections": timed_connections,
        "timed_fully_mapped": timed_fully_mapped,
    }
    if atom_timing_pin_labeled:
        summary.update(
            {
                "atom_timing_pin_labeled": atom_timing_pin_labeled,
                "atom_timing_pin_mapped": atom_timing_pin_mapped,
                "atom_timing_pin_unmapped": atom_timing_pin_labeled - atom_timing_pin_mapped,
            }
        )
    return summary


def pack(args: argparse.Namespace) -> None:
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    inputs = {
        "packed_netlist": args.netlist.resolve(),
        "reference_place": args.place.resolve(),
        "rr_graph": args.rr_graph.resolve(),
        "architecture": args.architecture.resolve(),
        "native_macros": args.native_macros.resolve(),
    }
    if args.connections:
        inputs["connections"] = args.connections.resolve()
    if args.timing:
        inputs["timing"] = args.timing.resolve()
    if args.constraints:
        inputs["constraints"] = args.constraints.resolve()
    if args.vpr_constraints:
        inputs["vpr_constraints"] = args.vpr_constraints.resolve()

    place_header, place_rows = parse_place(inputs["reference_place"])
    placement_by_name = {row["name"]: row for row in place_rows}
    constraint_summary: dict[str, Any]
    if "vpr_constraints" in inputs:
        constraints, constraint_summary = parse_vpr_constraints(
            inputs["vpr_constraints"], inputs["packed_netlist"]
        )
    else:
        constraints = load_constraints(inputs.get("constraints"))
        constraint_summary = {
            "source": "json" if "constraints" in inputs else "none",
            "constrained_clusters": len(constraints["regions"]),
            "coordinate_fixed_clusters": len(constraints.get("fixed_locations", {})),
            "fully_fixed_clusters": len(constraints["fixed"]),
        }
    native_macro_by_block, native_macro_summary = parse_vpr_place_macros(
        inputs["native_macros"], placement_by_name
    )
    netlist_attributes, blocks, net_pins = parse_packed_netlist(
        inputs["packed_netlist"], placement_by_name, constraints, native_macro_by_block
    )
    architecture_hash = sha256(inputs["architecture"])
    if netlist_attributes.get("architecture_id") != f"SHA256:{architecture_hash}":
        raise ContractError("architecture does not match the packed-netlist architecture id")
    connection_map, _timing = parse_connections(inputs.get("connections"), inputs.get("timing"))
    endpoint_node_ids = {
        connection[key]
        for routed in connection_map.values()
        for connection in routed["connections"]
        for key in ("source_rr_node", "sink_rr_node")
    }
    sites, block_types, endpoint_locations = parse_rr_sites(inputs["rr_graph"], endpoint_node_ids)
    nets = make_nets(net_pins, connection_map)
    endpoint_mapping = annotate_connection_blocks(
        nets, blocks, endpoint_locations, block_types
    )

    outputs: dict[str, dict[str, Any]] = {}
    for filename, rows in (("blocks.jsonl", blocks), ("sites.jsonl", sites), ("nets.jsonl", nets)):
        count, digest = write_jsonl(output / filename, rows)
        outputs[filename] = {"count": count, "sha256": digest}
    manifest = {
        "schema": SCHEMA,
        "vpr": {
            "revision": args.vpr_revision,
            "seed": args.seed,
            "channel_width": args.channel_width,
            "command": args.vpr_command,
        },
        "inputs": {
            key: {"path": str(path), "sha256": sha256(path)} for key, path in inputs.items()
        },
        "outputs": outputs,
        "placement_header": place_header,
        "packed_netlist": netlist_attributes,
        "placement_macros": native_macro_summary,
        "placement_constraints": constraint_summary,
        "connection_endpoint_mapping": endpoint_mapping,
        "rr_block_types": block_types,
        "compatibility": "logical_type must equal physical_type",
    }
    dump_json(output / "manifest.json", manifest)
    report = validate_contract(output, inputs["reference_place"])
    report["reference_unchanged"] = True
    dump_json(output / "reference_validation.json", report)
    print(json.dumps({"status": "pass", "output": str(output), **report}, sort_keys=True))


def load_contract(directory: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest.get("schema") != SCHEMA:
        raise ContractError(f"unsupported contract schema {manifest.get('schema')!r}")
    collections = []
    for filename in ("blocks.jsonl", "sites.jsonl", "nets.jsonl"):
        expected = manifest["outputs"][filename]
        path = directory / filename
        if sha256(path) != expected["sha256"]:
            raise ContractError(f"contract hash mismatch: {filename}")
        rows = read_jsonl(path)
        if len(rows) != expected["count"]:
            raise ContractError(f"contract count mismatch: {filename}")
        collections.append(rows)
    return manifest, collections[0], collections[1], collections[2]


def location(record: dict[str, Any]) -> tuple[int, int, int, int]:
    return record["x"], record["y"], record["subtile"], record["layer"]


def in_region(block: dict[str, Any], loc: tuple[int, int, int, int]) -> bool:
    region = block.get("region")
    if region is None:
        return True
    x, y, subtile, layer = loc
    if region and all(isinstance(value, int) for value in region):
        if not (region[0] <= x <= region[2] and region[1] <= y <= region[3]):
            return False
        return len(region) == 4 or layer == region[4]
    return any(
        item["xmin"] <= x <= item["xmax"]
        and item["ymin"] <= y <= item["ymax"]
        and item["layer_low"] <= layer <= item["layer_high"]
        and (item["subtile"] == -1 or item["subtile"] == subtile)
        for item in region
    )


def matches_fixed(block: dict[str, Any], loc: tuple[int, int, int, int]) -> bool:
    if not block.get("fixed"):
        return True
    fixed_location = block.get("fixed_location")
    if fixed_location is None:
        return loc == location(block["initial"])
    return all(
        fixed_location[key] is None or loc[index] == fixed_location[key]
        for index, key in enumerate(("x", "y", "subtile", "layer"))
    )


def validate_contract(directory: Path, place_path: Path) -> dict[str, Any]:
    _manifest, blocks, sites, _nets = load_contract(directory)
    _header, rows = parse_place(place_path)
    by_name = {row["name"]: row for row in rows}
    expected = {block["name"] for block in blocks}
    actual = set(by_name)
    errors: list[str] = []
    if missing := sorted(expected - actual):
        errors.append(f"missing blocks: {missing[:5]}")
    if extra := sorted(actual - expected):
        errors.append(f"unknown blocks: {extra[:5]}")
    site_by_location = {location(site): site for site in sites}
    occupied: dict[tuple[int, int, int, int], str] = {}
    block_by_name = {block["name"]: block for block in blocks}
    for name in sorted(expected & actual):
        block = block_by_name[name]
        loc = location(by_name[name])
        site = site_by_location.get(loc)
        if site is None:
            errors.append(f"{name}: location {loc} is not a root site/subtile")
            continue
        if site["physical_type"] != block["logical_type"]:
            errors.append(
                f"{name}: logical type {block['logical_type']} is incompatible with {site['physical_type']} at {loc}"
            )
        if loc in occupied:
            errors.append(f"{name}: site {loc} is already occupied by {occupied[loc]}")
        else:
            occupied[loc] = name
        if not in_region(block, loc):
            errors.append(f"{name}: location {loc} violates region {block['region']}")
        if not matches_fixed(block, loc):
            errors.append(
                f"{name}: location {loc} violates fixed dimensions "
                f"{block.get('fixed_location') or location(block['initial'])}"
            )

    macro_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for block in blocks:
        if block.get("macro"):
            macro_groups[block["macro"]["id"]].append(block)
    for macro_id, members in sorted(macro_groups.items()):
        present = [member for member in members if member["name"] in by_name]
        if len(present) != len(members):
            continue
        anchor_values = set()
        for member in members:
            x, y, subtile, layer = location(by_name[member["name"]])
            macro = member["macro"]
            anchor_values.add(
                (x - macro["dx"], y - macro["dy"], subtile - macro["dsubtile"], layer - macro["dlayer"])
            )
        if len(anchor_values) != 1:
            errors.append(f"macro {macro_id}: members do not preserve their declared relative shape")
    if errors:
        raise ContractError("; ".join(errors[:12]))
    return {
        "schema": PLACE_SCHEMA,
        "legal": True,
        "blocks": len(blocks),
        "occupied_sites": len(occupied),
        "macros": len(macro_groups),
        "placement_sha256": sha256(place_path),
    }


def net_adjacency(nets: list[dict[str, Any]]) -> tuple[dict[int, list[int]], dict[int, int]]:
    block_nets: dict[int, list[int]] = defaultdict(list)
    weights: dict[int, int] = {}
    for net in nets:
        members = sorted({pin["block_id"] for pin in net["pins"]})
        if len(members) < 2:
            continue
        net_id = net["net_id"]
        weights[net_id] = max(1, int(net.get("criticality_q", 0)))
        for block_id in members:
            block_nets[block_id].append(net_id)
    return block_nets, weights


def legalize(directory: Path, output_place: Path, input_place: Path | None = None) -> dict[str, Any]:
    manifest, blocks, sites, nets = load_contract(directory)
    targets = {block["block_id"]: location(block["initial"]) for block in blocks}
    input_place_sha256 = None
    if input_place is not None:
        _input_header, input_rows = parse_place(input_place)
        input_by_name = {row["name"]: row for row in input_rows}
        expected_names = {block["name"] for block in blocks}
        if set(input_by_name) != expected_names:
            missing = sorted(expected_names - set(input_by_name))
            extra = sorted(set(input_by_name) - expected_names)
            raise ContractError(f"input placement block set mismatch; missing={missing[:3]}, extra={extra[:3]}")
        targets = {
            block["block_id"]: location(input_by_name[block["name"]]) for block in blocks
        }
        input_place_sha256 = sha256(input_place)
    site_by_location = {location(site): site for site in sites}
    sites_by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for site in sites:
        sites_by_type[site["physical_type"]].append(site)
    for rows in sites_by_type.values():
        rows.sort(key=lambda site: (site["layer"], site["y"], site["x"], site["subtile"]))

    block_by_id = {block["block_id"]: block for block in blocks}
    block_by_name = {block["name"]: block for block in blocks}
    block_nets, net_weights = net_adjacency(nets)
    net_members = {
        net["net_id"]: sorted({pin["block_id"] for pin in net["pins"]}) for net in nets
    }
    assigned: dict[int, tuple[int, int, int, int]] = {}
    occupied: set[tuple[int, int, int, int]] = set()

    def incremental_net_cost(block: dict[str, Any], loc: tuple[int, int, int, int]) -> int:
        x, y, _subtile, _layer = loc
        total = 0
        for net_id in block_nets.get(block["block_id"], []):
            weight = net_weights[net_id]
            for peer_id in net_members[net_id]:
                if peer_id in assigned:
                    px, py, _ps, _pl = assigned[peer_id]
                    total += weight * (abs(x - px) + abs(y - py))
        return total

    def candidate_ok(block: dict[str, Any], loc: tuple[int, int, int, int]) -> bool:
        site = site_by_location.get(loc)
        return bool(
            site
            and site["physical_type"] == block["logical_type"]
            and loc not in occupied
            and in_region(block, loc)
            and matches_fixed(block, loc)
        )

    macro_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    independent: list[dict[str, Any]] = []
    for block in blocks:
        if block.get("macro"):
            macro_groups[block["macro"]["id"]].append(block)
        else:
            independent.append(block)

    def place_macro(macro_id: str, members: list[dict[str, Any]]) -> None:
        members.sort(key=lambda block: (block["macro"]["dx"], block["macro"]["dy"], block["block_id"]))
        first = members[0]
        candidates: list[tuple[tuple[int, ...], list[tuple[dict[str, Any], tuple[int, int, int, int]]]]] = []
        for first_site in sites_by_type.get(first["logical_type"], []):
            fx, fy, fs, fl = location(first_site)
            fm = first["macro"]
            anchor = (fx - fm["dx"], fy - fm["dy"], fs - fm["dsubtile"], fl - fm["dlayer"])
            trial = []
            valid = True
            for member in members:
                macro = member["macro"]
                loc = (
                    anchor[0] + macro["dx"],
                    anchor[1] + macro["dy"],
                    anchor[2] + macro["dsubtile"],
                    anchor[3] + macro["dlayer"],
                )
                if not candidate_ok(member, loc) or any(previous_loc == loc for _previous, previous_loc in trial):
                    valid = False
                    break
                trial.append((member, loc))
            if valid:
                displacement = sum(
                    abs(loc[0] - targets[member["block_id"]][0])
                    + abs(loc[1] - targets[member["block_id"]][1])
                    + abs(loc[2] - targets[member["block_id"]][2])
                    for member, loc in trial
                )
                net_cost = sum(incremental_net_cost(member, loc) for member, loc in trial)
                candidates.append(((displacement, net_cost, anchor[3], anchor[1], anchor[0], anchor[2]), trial))
        if not candidates:
            raise ContractError(f"no legal placement for macro {macro_id}")
        _score, winner = min(candidates, key=lambda item: item[0])
        for member, loc in winner:
            assigned[member["block_id"]] = loc
            occupied.add(loc)

    for macro_id in sorted(macro_groups, key=lambda value: (not any(b.get("fixed") for b in macro_groups[value]), value)):
        place_macro(macro_id, macro_groups[macro_id])

    independent.sort(key=lambda block: (not block.get("fixed"), block["block_id"], block["name"]))
    for block in independent:
        target = targets[block["block_id"]]
        if candidate_ok(block, target):
            assigned[block["block_id"]] = target
            occupied.add(target)
            continue
        candidates = []
        for site in sites_by_type.get(block["logical_type"], []):
            loc = location(site)
            if not candidate_ok(block, loc):
                continue
            displacement = abs(loc[0] - target[0]) + abs(loc[1] - target[1]) + abs(loc[2] - target[2])
            score = (displacement, incremental_net_cost(block, loc), loc[3], loc[1], loc[0], loc[2])
            candidates.append((score, loc))
        if not candidates:
            raise ContractError(f"no legal site for block {block['name']!r} ({block['logical_type']})")
        _score, winner = min(candidates)
        assigned[block["block_id"]] = winner
        occupied.add(winner)

    header = manifest.get("placement_header", {})
    lines = []
    if header.get("netlist"):
        lines.append(header["netlist"])
    if header.get("array_size"):
        lines.append(header["array_size"])
    lines.extend(["", "#block name\tx\ty\tsubblk\tlayer\tblock number", "#----------\t--\t--\t------\t-----\t------------"])
    for block in sorted(blocks, key=lambda item: (item["block_id"], item["name"])):
        x, y, subtile, layer = assigned[block["block_id"]]
        lines.append(f"{block['name']}\t\t{x}\t{y}\t{subtile}\t{layer}\t#{block['block_id']}")
    output_place.parent.mkdir(parents=True, exist_ok=True)
    output_place.write_text("\n".join(lines) + "\n")
    report = validate_contract(directory, output_place)
    moved_from_reference = sum(
        assigned[block["block_id"]] != location(block["initial"]) for block in blocks
    )
    moved_from_input = sum(
        assigned[block["block_id"]] != targets[block["block_id"]] for block in blocks
    )
    report.update(
        {
            "moved_blocks": moved_from_reference,
            "moved_from_reference": moved_from_reference,
            "moved_from_input": moved_from_input,
            "input_place_sha256": input_place_sha256,
            "deterministic_tie_break": "displacement,net_cost,layer,y,x,subtile",
        }
    )
    return report


def command_validate(args: argparse.Namespace) -> None:
    report = validate_contract(args.contract.resolve(), args.place.resolve())
    if args.output:
        dump_json(args.output.resolve(), report)
    print(json.dumps(report, sort_keys=True))


def command_legalize(args: argparse.Namespace) -> None:
    report = legalize(
        args.contract.resolve(),
        args.output.resolve(),
        args.input_place.resolve() if args.input_place else None,
    )
    if args.report:
        dump_json(args.report.resolve(), report)
    print(json.dumps(report, sort_keys=True))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    pack_parser = commands.add_parser("pack", help="pack VPR artifacts into a TilePlace contract")
    pack_parser.add_argument("--netlist", type=Path, required=True)
    pack_parser.add_argument("--place", type=Path, required=True)
    pack_parser.add_argument("--rr-graph", type=Path, required=True)
    pack_parser.add_argument("--architecture", type=Path, required=True)
    pack_parser.add_argument("--native-macros", type=Path, required=True)
    pack_parser.add_argument("--connections", type=Path)
    pack_parser.add_argument("--timing", type=Path)
    constraint_group = pack_parser.add_mutually_exclusive_group()
    constraint_group.add_argument("--constraints", type=Path, help="TilePlace JSON constraints")
    constraint_group.add_argument(
        "--vpr-constraints", type=Path, help="native VPR placement-constraints XML"
    )
    pack_parser.add_argument("--output", type=Path, required=True)
    pack_parser.add_argument("--vpr-revision", required=True)
    pack_parser.add_argument("--seed", type=int, required=True)
    pack_parser.add_argument("--channel-width", type=int, required=True)
    pack_parser.add_argument("--vpr-command", nargs="+", required=True)
    pack_parser.set_defaults(handler=pack)

    legalize_parser = commands.add_parser("legalize", help="run the unlimited-size CPU golden legalizer")
    legalize_parser.add_argument("--contract", type=Path, required=True)
    legalize_parser.add_argument("--output", type=Path, required=True)
    legalize_parser.add_argument("--input-place", type=Path)
    legalize_parser.add_argument("--report", type=Path)
    legalize_parser.set_defaults(handler=command_legalize)

    validate_parser = commands.add_parser("validate", help="fail-closed placement legality validation")
    validate_parser.add_argument("--contract", type=Path, required=True)
    validate_parser.add_argument("--place", type=Path, required=True)
    validate_parser.add_argument("--output", type=Path)
    validate_parser.set_defaults(handler=command_validate)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        args.handler(args)
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"tileplace_vpr: ERROR: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
