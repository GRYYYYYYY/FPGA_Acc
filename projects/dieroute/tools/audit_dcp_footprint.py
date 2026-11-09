#!/usr/bin/env python3
"""Join independent footprint checks to prior native inventory and SLL report."""
import argparse
import csv
from itertools import zip_longest
import json
import mmap
from pathlib import Path
import re
import shutil
import struct
import subprocess
import time

from run_native_case import sha256


def check_hashes(paths):
    for path, expected in paths.items():
        if sha256(Path(path)) != expected:
            raise ValueError("changed artifact: " + str(path))


def main():
    if not __debug__:
        raise RuntimeError("run without Python optimization; audit assertions are mandatory")
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("producer", "inventory", "utilization", "verifier", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    out = args.output.resolve()
    for name in (Path(__file__).name, "run_native_case.py", "verify_dcp_footprint.cpp"):
        shutil.copyfile(Path(__file__).with_name(name), out / name)
    args.producer = args.producer.resolve()
    args.inventory = args.inventory.resolve()
    export = args.producer / "footprint"
    prod = json.loads((args.producer / "manifest.json").read_text())
    inv = json.loads((args.inventory.parent / "manifest.json").read_text())
    assert prod["schema"] == "dieroute.dcp_footprint_run.v1"
    assert inv["schema"] == "dieroute.dcp_inventory.v3"
    assert prod["status"] == inv["status"] == "passed"
    assert prod["inputs_unchanged"] and inv["inputs_unchanged"]
    assert prod["compile_returncode"] == prod["returncode"] == 0
    assert prod["inputs"] == {v["path"]: v["sha256"] for v in inv["inputs"].values()}
    assert prod["runtime"] == inv["runtime"]
    record = {"schema": "dieroute.dcp_footprint_cross_audit.v1", "status": "running", "started_ns": time.time_ns(),
              "producer_manifest": str(args.producer / "manifest.json"),
              "inventory_manifest": str(args.inventory.parent / "manifest.json"),
              "producer_manifest_sha256": sha256(args.producer / "manifest.json"),
              "inventory_manifest_sha256": sha256(args.inventory.parent / "manifest.json"),
              "verifier_sha256": sha256(args.verifier),
              "utilization": str(args.utilization.resolve()), "utilization_sha256": sha256(args.utilization)}
    manifest = out / "manifest.json"

    def save():
        temp = out / "manifest.tmp"
        temp.write_text(json.dumps(record, indent=2) + "\n")
        temp.replace(manifest)

    save()
    try:
        check_hashes({args.producer / f: h for f, h in prod["artifacts"].items()})
        check_hashes(prod["inputs"])
        for name in ("jars", "classpath_classes"):
            assert prod[name] == inv[name]
            check_hashes(prod[name])
        # v1 producer omitted runtime hashes. Match the exact same runtime to
        # the previously frozen native inventory, and retain those hashes here.
        record["runtime_data"] = inv["runtime_data"]
        check_hashes(record["runtime_data"])
        for name in ("nets.csv", "pins.csv"):
            assert sha256(args.inventory / name) == inv["artifacts"]["inventory/" + name]
        cmd = [str(args.verifier.resolve()), str(export), str(out / "binary_audit")]
        record["command"] = cmd
        with (out / "verify.log").open("w") as log:
            proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            record["pid"] = proc.pid
            save()
            record["returncode"] = proc.wait()
        assert record["returncode"] == 0, "binary verifier failed"
        audit = json.loads((out / "binary_audit/audit.json").read_text())
        summary = json.loads((export / "summary.json").read_text())
        for name in summary.keys() & audit.keys() - {"schema", "scope"}:
            assert summary[name] == audit[name], name
        assert summary["missing_node_encounters"] == audit["missing_pin_nodes"] + audit["missing_pip_endpoints"]
        with (export / "nets.bin").open("rb") as f, (export / "nodes.bin").open("rb") as nf, (export / "pins.bin").open("rb") as pf:
            nets = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            nodes = mmap.mmap(nf.fileno(), 0, access=mmap.ACCESS_READ)
            pins = mmap.mmap(pf.fileno(), 0, access=mmap.ACCESS_READ)
            identities = []
            with (export / "nets.csv").open() as s, (args.inventory / "nets.csv").open() as t:
                for i, pair in enumerate(zip_longest(csv.DictReader(s), csv.DictReader(t))):
                    a, b = pair
                    assert a is not None and b is not None, "net inventory length"
                    n = struct.unpack_from("<16I", nets, i * 64)
                    assert int(a["id"]) == i and a["name"] == b["net"], "net name/ID"
                    assert int(a["reason_mask"]) == n[0]
                    assert (a["candidate"] == "true") == (n[0] == 0)
                    assert (int(a["source_node"]) & 0xffffffff) == n[1]
                    for column, index in (("outputs", 11), ("inputs", 12), ("pin_count", 4), ("pip_count", 6), ("owned_nodes", 10), ("tasks", 8)):
                        assert int(a[column]) == n[index], column
                    assert n[4] == int(b["pins"]) and n[6] == int(b["pips"])
                    assert bool(n[0] & 1) == (b["static"] == "true")
                    assert bool(n[0] & 2) == (b["clock"] == "true")
                    identities.append((b["net"], b["source_site"], b["source_pin"], int(b["source_slr"])))
            assert len(identities) == summary["nets"]
            pin_count = 0
            with (export / "pins.csv").open() as s, (args.inventory / "pins.csv").open() as t:
                for i, pair in enumerate(zip_longest(csv.DictReader(s), csv.DictReader(t))):
                    a, b = pair
                    assert a is not None and b is not None, "pin inventory length"
                    net_id, node_id, slr, output = struct.unpack_from("<4I", pins, i * 16)
                    identity = identities[net_id]
                    assert int(a["id"]) == i and int(a["net_id"]) == net_id
                    assert (int(a["node_id"]) & 0xffffffff) == node_id
                    assert identity[0] == b["net"]
                    assert all(a[k] == b[k] for k in ("site_inst", "site", "pin", "access_slr"))
                    assert a["output"] == b["is_output"] and (a["output"] == "true") == bool(output)
                    assert (int(a["access_slr"]) & 0xffffffff) == slr
                    if node_id != 0xffffffff:
                        assert struct.unpack_from("<I", nodes, node_id * 64 + 20)[0] == int(b["membership_mask"])
                    source_pin = struct.unpack_from("<I", nets, net_id * 64 + 8)[0]
                    if i == source_pin:
                        assert (a["site_inst"], a["pin"], int(a["access_slr"])) == identity[1:]
                    pin_count += 1
            assert pin_count == summary["pins"]
            nodes.close(); pins.close(); nets.close()
        text = args.utilization.read_text()
        total = int(re.search(r"\|\s*Total SLLs Used\s*\|\s*(\d+)", text)[1])
        by_boundary = {"3": int(re.search(r"\|\s*SLR1 <-> SLR0\s*\|\s*(\d+)", text)[1]),
                       "6": int(re.search(r"\|\s*SLR2 <-> SLR1\s*\|\s*(\d+)", text)[1])}
        assert audit["owned_cross_slr_laguna_nodes"] == total
        assert audit["sll_membership_counts"] == by_boundary
        assert sha256(args.verifier) == record["verifier_sha256"], "verifier changed during audit"
        record.update(status="passed", compared_nets=len(identities), compared_pins=pin_count,
                      native_sll_total=total, native_sll_boundaries=by_boundary,
                      scope="full used-resource footprint and prior native inventory consistency; no rerouting/QoR/board claim")
    except Exception as exc:
        record.update(status="failed", error=repr(exc))
        raise
    finally:
        record["finished_ns"] = time.time_ns()
        record["artifacts"] = {str(f.relative_to(out)): sha256(f) for f in sorted(out.rglob("*")) if f.is_file() and f != manifest}
        save()
    print(json.dumps({"manifest": str(manifest), "status": record["status"]}))


if __name__ == "__main__":
    main()
