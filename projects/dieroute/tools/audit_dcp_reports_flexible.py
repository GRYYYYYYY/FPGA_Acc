#!/usr/bin/env python3
"""Read archived native Vivado reports, optionally compare a no-op round trip.

Default DRC and timing summary do not replace a full implementation/bitstream
flow; in particular this report set does not include report_bus_skew.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

from run_native_case import sha256


def native_reports(directory):
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest["status"] != "reports_generated" or manifest["returncode"] != 0:
        raise ValueError("native report command did not finish successfully")
    for name, digest in manifest["artifacts"].items():
        if sha256(directory / name) != digest:
            raise ValueError("native report artifact changed: " + name)
    if sha256(Path(manifest["input"])) != manifest["input_sha256"]:
        raise ValueError("checkpoint changed after native checking")
    for name, digest in manifest.get("dependencies", {}).items():
        if sha256(Path(name)) != digest:
            raise ValueError("native checkpoint dependency changed: " + name)
    reports = directory / "reports"
    if not (reports / "checks_completed.txt").is_file():
        raise ValueError("missing native completion marker")
    design = dict(line.split("=", 1) for line in (reports / "design.txt").read_text().splitlines())
    route = {label.strip(): int(value) for label, value in re.findall(
        r"# of ([^.\n]+)\.+\s*:\s*(\d+)\s*:", (reports / "route_status.rpt").read_text())}
    required = {"logical nets", "routable nets", "fully routed nets", "nets with routing errors"}
    if not required <= route.keys():
        raise ValueError("missing native route status fields")
    text = (reports / "timing_summary.rpt").read_text()
    timing_rows = re.search(r"^\s*WNS\(ns\)[^\n]*\n[^\n]*\n([^\n]+)", text, re.M)
    if not timing_rows:
        raise ValueError("missing design timing summary row")
    values = timing_rows[1].split()
    names = ("wns_ns", "tns_ns", "setup_failing_endpoints", "setup_total_endpoints",
             "whs_ns", "ths_ns", "hold_failing_endpoints", "hold_total_endpoints",
             "wpws_ns", "tpws_ns", "pulse_failing_endpoints", "pulse_total_endpoints")
    if len(values) != len(names):
        raise ValueError("unexpected timing summary width")
    timing = {name: (int(value) if "endpoints" in name else float(value)) for name, value in zip(names, values)}
    checks = {name: int(count) for name, count in re.findall(r"^\d+\. checking (\w+) \((\d+)\)", text, re.M)}
    drc_text = (reports / "drc.rpt").read_text()
    total = re.search(r"Violations found:\s*(\d+)", drc_text)
    if not total:
        raise ValueError("missing DRC total")
    rules, severities = {}, Counter()
    for line in drc_text.splitlines():
        cols = [c.strip() for c in line.split("|")]
        if len(cols) == 6 and re.fullmatch(r"[A-Z0-9]+-\d+", cols[1]):
            if cols[1] in rules or cols[2] not in {"Warning", "Advisory", "Critical Warning", "Error"}:
                raise ValueError("unexpected or duplicate DRC summary rule")
            count = int(cols[4])
            rules[cols[1]] = {"severity": cols[2], "count": count}
            severities[cols[2]] += count
    if sum(severities.values()) != int(total[1]):
        raise ValueError("DRC rows do not account for the reported total")
    util_text = (reports / "utilization.rpt").read_text()
    sll = {name.strip(): int(value) for name, value in re.findall(
        r"^\|\s*(SLR\d+ <-> SLR\d+|Total SLLs Used)\s*\|\s*(\d+)\s*\|", util_text, re.M)}
    if "Total SLLs Used" not in sll:
        raise ValueError("missing native SLL utilization")
    primitives_text = re.search(r"^\d+\. Primitives\n-+\n(.*?)^\d+\. Black Boxes", util_text, re.M | re.S)
    if not primitives_text:
        raise ValueError("missing primitive utilization table")
    primitives = {name.strip(): int(value) for name, value in re.findall(
        r"^\|\s*([^|]+)\|\s*(\d+)\s*\|", primitives_text[1], re.M)}
    return {"directory": str(directory.resolve()), "manifest_sha256": sha256(directory / "manifest.json"),
            "design": design, "route": route, "timing": timing, "timing_checks": checks,
            "drc": {"rules": rules, "severities": dict(severities), "total": int(total[1])},
            "sll_utilization": sll, "primitive_utilization": primitives,
            "fully_routed_without_errors": route["routable nets"] > 0 and
            route["routable nets"] == route["fully routed nets"] and route["nets with routing errors"] == 0,
            "no_drc_errors_or_critical_warnings": not severities["Error"] and not severities["Critical Warning"]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("baseline", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--roundtrip", type=Path)
    args = p.parse_args()
    baseline = native_reports(args.baseline)
    result = {"schema": "dieroute.native_dcp_audit.v1", "baseline": baseline,
              "board_result": False, "routes_recomputed": False,
              "scope": "default_native_DRC_route_status_and_timing_summary",
              "not_checked": ["bus_skew", "bitstream_generation", "board_execution", "DieRoute_rerouting"]}
    ok = baseline["fully_routed_without_errors"] and baseline["no_drc_errors_or_critical_warnings"]
    if args.roundtrip:
        other = native_reports(args.roundtrip)
        result["roundtrip"] = other
        equal = {name: baseline[name] == other[name] for name in
                 ("route", "timing", "timing_checks", "drc", "sll_utilization", "primitive_utilization")}
        equal["design_size_and_part"] = all(baseline["design"][k] == other["design"][k] for k in ("part", "cells", "nets", "slrs"))
        result["comparison"] = equal
        result["all_compared_fields_equal"] = all(equal.values())
        ok = ok and result["all_compared_fields_equal"] and other["fully_routed_without_errors"] and other["no_drc_errors_or_critical_warnings"]
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
