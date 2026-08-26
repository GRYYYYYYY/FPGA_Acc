#!/usr/bin/env python3
"""Freeze auditable PersistRoute paper tables and figures from experiment logs."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "experiments" / "vpr9" / "baseline_runs"
OUTPUT = ROOT / "paper" / "generated"
VTR_ROOT = Path("/home/gry/.local/opt/vtr-9.0.0-src")

CASES = [
    ("VTR", "diffeq_seed1_cw200", "diffeq"),
    ("VTR", "frisc_seed1_cw200", "frisc"),
    ("VTR", "elliptic_seed1_cw200", "elliptic"),
    ("VTR", "clma_seed1_cw200", "clma"),
    ("Titan23", "titan23_neuron_seed3_cw300", "neuron"),
    ("Titan23", "titan23_stereo_vision_seed3_cw300", "stereo vision"),
    ("Koios 2.0", "koios_conv_layer_seed1_cw300", "conv layer"),
    ("Koios 2.0", "koios_attention_layer_seed1_cw300", "attention layer"),
    ("Koios 2.0", "koios_spmv_seed1_cw300", "SpMV"),
    ("Koios 2.0", "koios_softmax_seed1_cw300", "softmax"),
]

PATTERNS = {
    "blocks": r"Circuit Statistics:\s*\n\s*Blocks:\s*([0-9]+)",
    "nets": r"\n\s*Nets\s*:\s*([0-9]+)",
    "routing_iterations": r"Successfully routed after\s+([0-9]+)\s+routing iterations",
    "wirelength": r"Total wirelength:\s*([0-9]+)",
    "cpd_ns": r"Final critical path delay \(least slack\):\s*([0-9.]+)\s*ns",
    "pack_s": r"# Packing took\s*([0-9.]+)\s*seconds",
    "place_s": r"# Placement took\s*([0-9.]+)\s*seconds",
    "route_s": r"# Routing took\s*([0-9.]+)\s*seconds",
    "vpr_total_s": r"The entire flow of VPR took\s*([0-9.]+)\s*seconds",
    "vpr_max_rss_mib": r"The entire flow of VPR took.*?max_rss\s*([0-9.]+)\s*MiB",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(text: str) -> dict[str, int | float]:
    result: dict[str, int | float] = {}
    for key, pattern in PATTERNS.items():
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
        if not matches:
            raise RuntimeError(f"missing {key} in VPR log")
        value = matches[-1]
        result[key] = int(value) if key in {"blocks", "nets", "routing_iterations", "wirelength"} else float(value)
    return result


def load_run(baseline: str, case_id: str) -> tuple[dict, dict, Path, Path]:
    directory = RUNS / baseline / case_id
    record = json.loads((directory / "run.json").read_text(encoding="utf-8"))
    if record.get("status") != "pass" or record.get("returncode") != 0:
        raise RuntimeError(f"{baseline}/{case_id} did not pass")
    stdout = directory / "stdout.log"
    metrics = extract(stdout.read_text(encoding="utf-8", errors="replace"))
    metrics["wall_s"] = float(record["wall_s"])
    metrics["max_rss_mib"] = (
        float(record["max_rss_kib"]) / 1024.0
        if record.get("max_rss_kib") is not None
        else metrics["vpr_max_rss_mib"]
    )
    route = directory / "design.route"
    if not route.exists():
        raise RuntimeError(f"missing route file for {baseline}/{case_id}")
    header = route.open(encoding="utf-8", errors="replace").readline()
    placement = re.fullmatch(
        r"Placement_File:\s+(\S+)\s+Placement_ID:\s+SHA256:([0-9a-f]{64})\s*\n?", header
    )
    if placement is None:
        raise RuntimeError(f"invalid placement identity in {baseline}/{case_id}/design.route")
    place = directory / placement.group(1)
    if not place.is_file() or sha256(place) != placement.group(2):
        raise RuntimeError(f"route/placement identity mismatch for {baseline}/{case_id}")
    return record, metrics, route, place


def geometric_mean(values: list[float]) -> float:
    return math.exp(sum(math.log(value) for value in values) / len(values))


def frontend_provenance() -> list[dict]:
    include = VTR_ROOT / "vtr_flow" / "benchmarks" / "verilog" / "koios" / "hard_block_include.v"
    entries = []
    for name, log_name in [
        ("conv_layer", "koios_conv_layer_frontend_driver.log"),
        ("attention_layer", "koios_attention_layer_frontend_driver_pass.log"),
        ("spmv", "koios_spmv_frontend_driver_pass.log"),
        ("softmax", "koios_softmax_frontend_driver_pass.log"),
    ]:
        source = VTR_ROOT / "vtr_flow" / "benchmarks" / "verilog" / "koios" / f"{name}.v"
        blif = ROOT / "experiments" / "vpr9" / f"koios_{name}_frontend" / f"{name}.pre-vpr.blif"
        log = ROOT / "experiments" / "vpr9" / log_name
        text = log.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"OK \(took ([0-9.]+) seconds, overall memory peak ([0-9.]+) (MiB|GiB)", text)
        if match is None or "Exit status: 0" not in text:
            raise RuntimeError(f"Koios frontend did not pass: {name}")
        peak = float(match.group(2)) * (1024.0 if match.group(3) == "GiB" else 1.0)
        entries.append({
            "case": name,
            "flow": "Parmys -> ABC -> VPR",
            "status": "pass",
            "wall_s": float(match.group(1)),
            "max_rss_mib": peak,
            "rtl_sha256": sha256(source),
            "hard_block_include_sha256": sha256(include),
            "pre_vpr_blif_sha256": sha256(blif),
            "driver_log_sha256": sha256(log),
        })
    return entries


def evidence_sources() -> dict[str, str]:
    names = [
        "accelerated_pathfinder_hw_emu_2026-08-26.json",
        "cufr_logicnets_jscl_2026-08-24.json",
        "fpga24_logicnets_jscl_2026-08-24.json",
        "hls_2022_2_u280.json",
        "hw_emu_2022_2_u280.json",
        "rwroute_logicnets_jscl_2026-08-24.json",
        "timing_criticality_2026-08-26.json",
        "timing_priority_frisc_2026-08-27.json",
        "vitis_link_2022_2_u280.json",
        "vpr9_baseline_suite_2026-08-24.json",
        "vpr9_titan23_koios_2026-08-24.json",
    ]
    return {name: sha256(ROOT / "experiments" / name) for name in names}


def latex(value: str) -> str:
    return value.replace("_", r"\_").replace("%", r"\%")


def write_baseline_table(rows: list[dict]) -> None:
    lines = [
        r"\begin{tabular}{llrrrrrr}",
        r"\toprule",
        r"Suite & Circuit & Blocks & Nets & Route iters. & CPD (ns) & Flow speedup & Route speedup \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(
            f"{latex(row['suite'])} & {latex(row['circuit'])} & {row['blocks']} & {row['nets']} & "
            f"{row['routing_iterations']} & {row['cpd_ns']:.3f} & {row['whole_flow_speedup']:.3f}$\\times$ & "
            f"{row['route_stage_speedup']:.3f}$\\times$ \\\\"
        )
    lines += [
        r"\midrule",
        f"\multicolumn{{6}}{{r}}{{Geometric mean}} & "
        f"{geometric_mean([row['whole_flow_speedup'] for row in rows]):.3f}$\\times$ & "
        f"{geometric_mean([row['route_stage_speedup'] for row in rows]):.3f}$\\times$" + r" \\",
        r"\bottomrule",
        r"\end{tabular}",
    ]
    (OUTPUT / "cpu_baseline_table.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_speedup_svg(rows: list[dict]) -> None:
    width, left, right, top, row_h = 1000, 210, 40, 70, 42
    height = top + row_h * len(rows) + 70
    plot_w = width - left - right
    maximum = max(1.5, max(max(r["whole_flow_speedup"], r["route_stage_speedup"]) for r in rows) * 1.08)
    x = lambda value: left + plot_w * value / maximum
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#222}.label{font-size:14px}.tick{font-size:12px;fill:#555}.title{font-size:19px;font-weight:600}.legend{font-size:13px}</style>',
        '<text x="500" y="28" text-anchor="middle" class="title">Paired VPR CPU baseline speedup (16 workers / 1 worker)</text>',
    ]
    for tick in [0, 0.5, 1.0, 1.5]:
        if tick > maximum:
            continue
        xpos = x(tick)
        parts.append(f'<line x1="{xpos:.1f}" y1="{top-18}" x2="{xpos:.1f}" y2="{height-50}" stroke="#ddd"/>')
        parts.append(f'<text x="{xpos:.1f}" y="{height-30}" text-anchor="middle" class="tick">{tick:.1f}×</text>')
    parts.append(f'<line x1="{x(1):.1f}" y1="{top-18}" x2="{x(1):.1f}" y2="{height-50}" stroke="#333" stroke-dasharray="4 3"/>')
    for index, row in enumerate(rows):
        y = top + index * row_h
        parts.append(f'<text x="{left-10}" y="{y+16}" text-anchor="end" class="label">{row["circuit"]}</text>')
        parts.append(f'<rect x="{left}" y="{y+2}" width="{max(0,x(row["whole_flow_speedup"])-left):.1f}" height="13" fill="#4C78A8"/>')
        parts.append(f'<rect x="{left}" y="{y+19}" width="{max(0,x(row["route_stage_speedup"])-left):.1f}" height="13" fill="#F58518"/>')
    parts += [
        f'<rect x="{left}" y="{height-19}" width="14" height="10" fill="#4C78A8"/><text x="{left+20}" y="{height-10}" class="legend">whole flow</text>',
        f'<rect x="{left+125}" y="{height-19}" width="14" height="10" fill="#F58518"/><text x="{left+145}" y="{height-10}" class="legend">routing stage</text>',
        '</svg>',
    ]
    (OUTPUT / "cpu_baseline_speedup.svg").write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_hardware_table() -> dict:
    report = json.loads((ROOT / "experiments" / "vitis_link_2022_2_u280.json").read_text(encoding="utf-8"))
    resources = report["post_synthesis_dynamic_region_resources"]
    timing = report["routed_timing"]
    rows = []
    for label, used, available in [
        ("LUT", resources["lut"], resources["available_lut"]),
        ("Register", resources["register"], resources["available_register"]),
        ("BRAM", resources["bram"], resources["available_bram"]),
        ("DSP", resources["dsp"], resources["available_dsp"]),
    ]:
        rows.append((label, used, available, 100.0 * used / available))
    lines = [r"\begin{tabular}{lrrr}", r"\toprule", r"Resource & Used & Available & Utilization \\", r"\midrule"]
    lines += [f"{label} & {used} & {available} & {percent:.2f}\\% \\\\" for label, used, available, percent in rows]
    lines += [r"\bottomrule", r"\end{tabular}"]
    (OUTPUT / "u280_resource_table.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "target": report["part"],
        "search_compute_units": report["topology"]["search_compute_units"],
        "commit_compute_units": report["topology"]["commit_compute_units"],
        "hbm_pseudo_channels": report["topology"]["hbm_pseudo_channels"],
        "requested_kernel_frequency_mhz": report["clocking"]["requested_kernel_frequency_mhz"],
        "wns_ns": timing["wns_ns"],
        "tns_ns": timing["tns_ns"],
        "whs_ns": timing["whs_ns"],
        "ths_ns": timing["ths_ns"],
        "resources": [{"name": label, "used": used, "available": available, "percent": percent} for label, used, available, percent in rows],
        "source_sha256": sha256(ROOT / "experiments" / "vitis_link_2022_2_u280.json"),
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for suite, case_id, circuit in CASES:
        serial_record, serial, serial_route, serial_place = load_run("vpr_serial", case_id)
        parallel_record, parallel, parallel_route, parallel_place = load_run("vpr_parallel", case_id)
        route_hash = sha256(serial_route)
        if route_hash != sha256(parallel_route):
            raise RuntimeError(f"serial/parallel route mismatch for {case_id}")
        place_hash = sha256(serial_place)
        if place_hash != sha256(parallel_place):
            raise RuntimeError(f"serial/parallel placement mismatch for {case_id}")
        for key in ("blocks", "nets", "routing_iterations", "wirelength", "cpd_ns"):
            if serial[key] != parallel[key]:
                raise RuntimeError(f"serial/parallel {key} mismatch for {case_id}")
        rows.append({
            "suite": suite,
            "case_id": case_id,
            "circuit": circuit,
            "blocks": serial["blocks"],
            "nets": serial["nets"],
            "routing_iterations": serial["routing_iterations"],
            "wirelength": serial["wirelength"],
            "cpd_ns": serial["cpd_ns"],
            "serial_wall_s": serial["wall_s"],
            "parallel_wall_s": parallel["wall_s"],
            "serial_route_s": serial["route_s"],
            "parallel_route_s": parallel["route_s"],
            "whole_flow_speedup": serial["wall_s"] / parallel["wall_s"],
            "route_stage_speedup": serial["route_s"] / parallel["route_s"],
            "serial_max_rss_mib": serial["max_rss_mib"],
            "parallel_max_rss_mib": parallel["max_rss_mib"],
            "route_sha256": route_hash,
            "place_sha256": place_hash,
            "serial_run_sha256": sha256(RUNS / "vpr_serial" / case_id / "run.json"),
            "parallel_run_sha256": sha256(RUNS / "vpr_parallel" / case_id / "run.json"),
            "input_sha256": serial_record["inputs"],
        })

    fieldnames = [key for key in rows[0] if key != "input_sha256"]
    with (OUTPUT / "cpu_baseline_results.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows({key: row[key] for key in fieldnames} for row in rows)

    summary = {
        "schema": "PERSISTROUTE_PAPER_ARTIFACTS_V1",
        "verified_date": "2026-08-27",
        "case_count": len(rows),
        "suite_case_counts": {suite: sum(row["suite"] == suite for row in rows) for suite in sorted({row["suite"] for row in rows})},
        "all_runs_passed": True,
        "all_paired_routes_and_qor_identical": True,
        "all_route_placement_identities_valid": True,
        "whole_flow_geomean_speedup": geometric_mean([row["whole_flow_speedup"] for row in rows]),
        "route_stage_geomean_speedup": geometric_mean([row["route_stage_speedup"] for row in rows]),
        "whole_flow_aggregate_speedup": sum(row["serial_wall_s"] for row in rows) / sum(row["parallel_wall_s"] for row in rows),
        "route_stage_aggregate_speedup": sum(row["serial_route_s"] for row in rows) / sum(row["parallel_route_s"] for row in rows),
        "koios_frontends": frontend_provenance(),
        "hardware_implementation": write_hardware_table(),
        "evidence_sources": evidence_sources(),
        "claim_boundary": "CPU VPR worker scaling is a baseline characterization, not measured U280 acceleration. Hardware-emulation wall time is excluded from performance claims; no physical U280 is available.",
        "cases": rows,
    }
    (OUTPUT / "paper_results.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_baseline_table(rows)
    write_speedup_svg(rows)
    hashes = {path.name: sha256(path) for path in sorted(OUTPUT.iterdir()) if path.is_file() and path.name != "SHA256SUMS"}
    (OUTPUT / "SHA256SUMS").write_text("".join(f"{digest}  {name}\n" for name, digest in hashes.items()), encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("case_count", "suite_case_counts", "whole_flow_geomean_speedup", "route_stage_geomean_speedup", "whole_flow_aggregate_speedup", "route_stage_aggregate_speedup")}, indent=2))


if __name__ == "__main__":
    main()
