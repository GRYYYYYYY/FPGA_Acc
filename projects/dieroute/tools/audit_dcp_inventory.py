#!/usr/bin/env python3
"""Audit exported physical pin/SLR inventory and optional serialization equality.

This checks the adapter's inventory, not complete native route legality or QoR.
"""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path

from run_native_case import sha256

FILES = ("nets.csv", "pins.csv", "cells.csv", "cell_pin_mapping.csv", "sites.csv")


def producer(path):
    manifest = path.parent / "manifest.json"
    m = json.loads(manifest.read_text())
    if m["schema"] != "dieroute.dcp_inventory.v3" or m["status"] != "passed" or not m["inputs_unchanged"]:
        raise ValueError("requires completed physical-BEL inventory v3")
    if m["steps"] != [{"name": "compile", "returncode": 0}, {"name": "inventory", "returncode": 0}]:
        raise ValueError("missing successful compilation and native inventory execution")
    hashes = {name: sha256(path / name) for name in FILES}
    for name, digest in hashes.items():
        if m["artifacts"]["inventory/" + name] != digest:
            raise ValueError("inventory changed after native producer completion")
    for entry in m["inputs"].values():
        if sha256(Path(entry["path"])) != entry["sha256"]:
            raise ValueError("inventory input changed after native producer completion")
    return {"manifest": str(manifest.resolve()), "manifest_sha256": sha256(manifest),
            "source_sha256": m["source_sha256"], "hashes": hashes}


def inventory(path):
    with (path / "nets.csv").open() as stream:
        nets = {}
        for row in csv.DictReader(stream):
            if row["net"] in nets:
                raise ValueError("duplicate net identity")
            nets[row["net"]] = row
    pin_counts, missing_counts, multi_counts, slrs = Counter(), Counter(), Counter(), {}
    source_seen = set()
    previous = None
    with (path / "pins.csv").open() as stream:
        for row in csv.DictReader(stream):
            name = row["net"]
            identity = (name, row["site_inst"], row["pin"])
            if previous is not None and identity <= previous:
                raise ValueError("duplicate or unsorted physical pin identity")
            previous = identity
            net = nets[name]
            access, mask = int(row["access_slr"]), int(row["membership_mask"])
            pin_counts[name] += 1
            if access < 0:
                missing_counts[name] += 1
            else:
                slrs.setdefault(name, set()).add(access)
            if row["canonical_node"]:
                if not 0 < mask < 256 or access not in range(8) or not (mask & (1 << access)):
                    raise ValueError("pin access lies outside native electrical node membership")
                if mask.bit_count() > 1:
                    multi_counts[name] += 1
            elif mask:
                raise ValueError("missing canonical node has nonzero membership")
            if row["site_inst"] == net["source_site"] and row["pin"] == net["source_pin"]:
                if row["is_output"] != "true" or access != int(net["source_slr"]):
                    raise ValueError("net source disagrees with physical pin record")
                if bool(row["canonical_node"]) != (net["source_node_present"] == "true"):
                    raise ValueError("net source connected-node status mismatch")
                source_seen.add(name)
    cross, patterns = [], Counter()
    for name, row in nets.items():
        actual = slrs.get(name, set())
        exported = set(map(int, row["pin_slrs"].split(";"))) if row["pin_slrs"] else set()
        if pin_counts[name] != int(row["pins"]) or missing_counts[name] != int(row["missing_pin_locations"]) or actual != exported:
            raise ValueError("net/pin inventory mismatch: " + name)
        if row["source_site"] and name not in source_seen:
            raise ValueError("declared source absent from physical pin inventory")
        if row["static"] == "false" and row["clock"] == "false" and len(actual) > 1:
            cross.append(row)
            patterns[row["pin_slrs"]] += 1
    cross.sort(key=lambda r: (int(r["pips"]), r["net"]))
    summary = {"nets": len(nets), "pins": sum(pin_counts.values()),
               "pips": sum(int(r["pips"]) for r in nets.values()),
               "signal_nets": sum(r["static"] == "false" and r["clock"] == "false" for r in nets.values()),
               "cross_slr_signal_nets": len(cross), "cross_slr_pin_patterns": dict(sorted(patterns.items())),
               "missing_pin_locations": sum(missing_counts.values()),
               "pins_on_multi_slr_nodes": sum(multi_counts.values()),
               "nets_without_source": sum(not r["source_site"] for r in nets.values()),
               "cross_slr_signals_without_source": sum(not r["source_site"] for r in cross)}
    return summary, cross


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("inventory", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--compare", type=Path)
    args = p.parse_args()
    provenance = producer(args.inventory)
    summary, cross = inventory(args.inventory)
    args.output.mkdir(parents=True, exist_ok=False)
    record = {"schema": "dieroute.dcp_inventory_audit.v2", "scope": "physical_inventory_not_native_legality",
              "input": str(args.inventory.resolve()), "summary": summary,
              "producer": provenance, "input_hashes": provenance["hashes"],
              "board_result": False, "routes_recomputed": False}
    if args.compare:
        other_provenance = producer(args.compare)
        if other_provenance["source_sha256"] != provenance["source_sha256"]:
            raise ValueError("cannot compare different inventory implementations")
        other, _ = inventory(args.compare)
        record["comparison"] = {"input": str(args.compare.resolve()), "summary": other,
                                "producer": other_provenance, "hashes": other_provenance["hashes"]}
        record["comparison"]["byte_equal"] = {name: record["input_hashes"][name] == record["comparison"]["hashes"][name]
                                               for name in FILES}
        record["comparison"]["all_inventory_equal"] = all(record["comparison"]["byte_equal"].values())
    if cross:
        with (args.output / "cross_slr_nets.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(cross[0]))
            writer.writeheader()
            writer.writerows(cross)
    (args.output / "audit.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    return 0 if not args.compare or record["comparison"]["all_inventory_equal"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
