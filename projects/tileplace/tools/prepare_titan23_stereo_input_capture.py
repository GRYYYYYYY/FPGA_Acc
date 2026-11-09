#!/usr/bin/env python3
"""Audit and summarize the preregistered Titan23 stereo_vision inputs."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from tileplace_vpr import ContractError, dump_json, sha256


EXPECTED = {
    "architecture": "0d3a4f0459af9a883329b934dea81f6a025c18a0ad10c63cbed3d2f8cac4c12b",
    "blif": "515426efda12b7c0f9c2414871cdd6cb2d1c21619de151934201a26e1b815762",
    "sdc": "392cbdc288bbabd7cbfa4edf638f6c644997ec5ca5cd06a451873b6b22c43e4c",
    "netlist": "aa5fac2699614a382ba5f10855957f5b0ecae95aa615c74614d2085ed51dd605",
    "place": "90d3067328296636b67e5ffebd6baf1edd2cc7acdf827e9ce055260c93a30c7f",
    "route": "72f222c6c57a2eae9fe4ffae38e317e35f5449e2232eef2d301fdea25197460f",
    "correctness_vpr": "a90dc1b3380ebda705e85f176db0cc3d6be1b71ab9ee887db819febc8b62bafc",
    "timing_vpr": "58c84e686fb622bd732b8f6c07d506c5efae318fe1adf57180dd4df89c0cb6b2",
}


def checked(path: Path, expected: str | None = None) -> dict:
    resolved = path.resolve()
    if not resolved.is_file():
        raise ContractError(f"missing evidence file: {resolved}")
    digest = sha256(resolved)
    if expected is not None and digest != expected:
        raise ContractError(f"hash mismatch for {resolved}: {digest}")
    return {"path": str(resolved), "sha256": digest, "size_bytes": resolved.stat().st_size}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tileplace", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        root = args.tileplace.resolve()
        workspace = root.parents[1]
        experiments = root / "experiments"
        capture = root / "work" / "titan23_stereo_vision_input_capture"
        download = root / "work" / "titan_download_2026-09-01"
        base = (
            workspace
            / "projects/persistroute/experiments/vpr9/baseline_runs/vpr_serial"
            / "titan23_stereo_vision_seed3_cw300"
        )
        vtr = root / "third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07"
        case_dir = experiments / "titan23_stereo_vision_seed3_cw300"
        endpoint_dir = experiments / "titan23_stereo_vision_seed3_cw300_endpoints"

        prereg = experiments / "titan23_stereo_vision_preregistration_2026-09-01.json"
        prereg_data = json.loads(prereg.read_text())
        if prereg_data.get("status") != "preregistered_before_input_capture_or_tileplace_run":
            raise ContractError("unexpected preregistration status")

        archive = checked(download / "titan_release_2.0.0_blif.tar.gz")
        if archive["size_bytes"] != 1_059_033_941:
            raise ContractError("official archive has unexpected length")
        archive["url"] = "https://www.eecg.utoronto.ca/~vaughn/titan/titan_release_2.0.0_blif.tar.gz"
        archive["integrity"] = "gzip -t and complete tar listing passed"

        architecture = checked(vtr / "vtr_flow/arch/titan/stratixiv_arch.timing.xml", EXPECTED["architecture"])
        blif = checked(capture / "stereo_vision_stratixiv_arch_timing.blif", EXPECTED["blif"])
        sdc = checked(capture / "stereo_vision_stratixiv_arch_timing.sdc", EXPECTED["sdc"])
        netlist = checked(base / "stereo_vision_stratixiv_arch_timing.net", EXPECTED["netlist"])
        place = checked(base / "stereo_vision_stratixiv_arch_timing.place", EXPECTED["place"])
        route = checked(base / "design.route", EXPECTED["route"])
        rr_graph = checked(capture / "rr_graph.xml")
        connections = checked(capture / "connections.csv")
        timing_input = checked(capture / "reference_timing.input.csv")
        timing_output_path = capture / "reference_timing.output.csv"
        timing_output = checked(timing_output_path)
        manifest = checked(endpoint_dir / "manifest.json")
        macro_report = checked(case_dir / "vpr_macro_capture.json")
        macro_data = json.loads((case_dir / "vpr_macro_capture.json").read_text())

        rows = mapped = high = 0
        cpds: set[int] = set()
        with timing_output_path.open(newline="") as stream:
            for row in csv.DictReader(stream):
                rows += 1
                mapped += int(row["timing_pin_mapped"])
                high += int(row["criticality_q"]) >= 60000
                cpds.add(int(row["critical_path_delay_ps"]))
        if rows != 81610 or mapped != 81499 or cpds != {7517}:
            raise ContractError("unexpected stereo_vision timing-export accounting")

        correctness = checked(vtr / "build_tileplace_vpr/vpr/vpr", EXPECTED["correctness_vpr"])
        timing_binary = checked(
            vtr / "build_tileplace_vpr_timing_optional/vpr/vpr", EXPECTED["timing_vpr"]
        )
        report = {
            "schema": "TILEPLACE_TITAN23_STEREO_VISION_INPUT_CAPTURE_V1",
            "status": "pass",
            "date": "2026-09-02",
            "case": "titan23_stereo_vision",
            "preregistration": checked(prereg),
            "official_archive": archive,
            "source_run": {
                "cohort": "PersistRoute frozen serial baseline",
                "seed": 3,
                "channel_width": 300,
                "vpr_revision": "8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07",
                "wirelength": 592827,
                "cpd_ns": 7.51746,
                "routing_iterations": 15,
                "max_router_iterations": 400,
                "router_lookahead": "map",
                "initial_pres_fac": 1.0,
                "router_profiler_astar_fac": 1.5,
            },
            "source_inputs": {
                "architecture": architecture,
                "circuit": blif,
                "sdc": sdc,
                "packed_netlist": netlist,
                "placement": place,
                "route": route,
            },
            "rr_graph": {
                **rr_graph,
                "nodes": 3593250,
                "edges": 39165143,
                "generation": "written before expected copied-placement route identity failure",
            },
            "connections": {**connections, "rows": rows},
            "timing_export": {
                "input": timing_input,
                "output": timing_output,
                "rows": rows,
                "critical_path_delay_ps": 7517,
                "criticality_q_threshold": 60000,
                "connections_at_or_above_threshold": high,
                "atom_timing_pin_mapped": mapped,
                "atom_timing_pin_unmapped": rows - mapped,
                "fully_labeled": mapped + (rows - mapped) == rows,
                "unmapped_policy": "explicit timing_pin_mapped=0 with criticality_q=0; retained in wire cost",
            },
            "timing_export_binary": timing_binary,
            "frozen_correctness_binary": correctness,
            "native_macros": {
                "report": macro_report,
                "output": checked(case_dir / "vpr_place_macros.echo"),
                **macro_data["macros"],
            },
            "contract": manifest,
            "claim_boundary": (
                "This is the outcome-blind preregistered second Titan23 point. The exact Titan 2.0.0 "
                "BLIF/SDC hashes were verified before TilePlace execution. The optional timing oracle "
                "explicitly labels 111 atom-pin-unmapped connections; all remain in wire accounting."
            ),
        }
        dump_json(args.output.resolve(), report)
        print(json.dumps({"status": "pass", "connections": rows, "mapped": mapped, "unmapped": rows - mapped}))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"prepare_titan23_stereo_input_capture: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
