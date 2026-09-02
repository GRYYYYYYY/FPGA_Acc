#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "tileplace_vpr.py"
SPEC = importlib.util.spec_from_file_location("tileplace_vpr", MODULE_PATH)
assert SPEC and SPEC.loader
tileplace_vpr = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tileplace_vpr)
sys.modules["tileplace_vpr"] = tileplace_vpr
RESEARCH_PATH = Path(__file__).parents[1] / "tools" / "tileplace_research.py"
RESEARCH_SPEC = importlib.util.spec_from_file_location("tileplace_research", RESEARCH_PATH)
assert RESEARCH_SPEC and RESEARCH_SPEC.loader
tileplace_research = importlib.util.module_from_spec(RESEARCH_SPEC)
RESEARCH_SPEC.loader.exec_module(tileplace_research)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_contract(directory: Path, blocks: list[dict], sites: list[dict], nets: list[dict] | None = None) -> None:
    directory.mkdir()
    outputs = {}
    for filename, rows in (
        ("blocks.jsonl", blocks),
        ("sites.jsonl", sites),
        ("nets.jsonl", nets or []),
    ):
        path = directory / filename
        path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows))
        outputs[filename] = {"count": len(rows), "sha256": digest(path)}
    manifest = {
        "schema": tileplace_vpr.SCHEMA,
        "outputs": outputs,
        "placement_header": {
            "netlist": "Netlist_File: synthetic.net Netlist_ID: SHA256:test",
            "array_size": "Array size: 700 x 2 logic blocks",
        },
    }
    (directory / "manifest.json").write_text(json.dumps(manifest))


def block(block_id: int, name: str, x: int, logical_type: str = "clb", **extra: object) -> dict:
    value = {
        "block_id": block_id,
        "name": name,
        "logical_type": logical_type,
        "mode": None,
        "initial": {"x": x, "y": 0, "subtile": 0, "layer": 0},
        "fixed": False,
        "region": None,
        "macro": None,
    }
    value.update(extra)
    return value


def site(site_id: int, x: int, physical_type: str = "clb") -> dict:
    return {
        "site_id": site_id,
        "physical_type": physical_type,
        "x": x,
        "y": 0,
        "subtile": 0,
        "layer": 0,
        "width": 1,
        "height": 1,
    }


def write_place(path: Path, header: dict[str, str], rows: list[dict]) -> None:
    lines = [header["netlist"], header["array_size"], "", "#block name x y subblk layer block number"]
    for row in rows:
        lines.append(
            f"{row['name']} {row['x']} {row['y']} {row['subtile']} {row['layer']} #{row['block_number']}"
        )
    path.write_text("\n".join(lines) + "\n")


class TilePlaceCpuGoldenTests(unittest.TestCase):
    def test_optional_atom_timing_mapping_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            connections = root / "connections.csv"
            timing = root / "timing.csv"
            connections.write_text(
                "id,net_id,net,source,sink,criticality_q,max_hops,priority,epoch\n"
                "0,0,n0,10,11,0,65535,0,0\n"
                "1,0,n0,10,12,0,65535,1,0\n"
            )
            timing.write_text(
                "task_id,criticality_q,delay_ps,slack_ps,critical_path_delay_ps,timing_pin_mapped\n"
                "0,65535,20,-10,100,1\n"
                "1,0,30,0,100,0\n"
            )
            connection_map, timing_rows = tileplace_vpr.parse_connections(connections, timing)
            routed = connection_map["n0"]["connections"]
            self.assertEqual([row["timing_pin_mapped"] for row in routed], [1, 0])
            self.assertEqual(timing_rows[1]["criticality_q"], 0)

    def test_critical_connection_distance_guard_rejects_regression(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract = root / "contract"
            blocks = [
                block(0, "source", 0),
                block(1, "critical_sink", 1, fixed=True),
                block(2, "wire_sink", 10, fixed=True),
            ]
            sites = [site(0, 0), site(1, 1), site(2, 5), site(3, 10)]
            nets = [
                {
                    "net_id": 0,
                    "criticality_q": 100,
                    "pins": [
                        {"block_id": 0, "role": "source"},
                        {"block_id": 1, "role": "sink"},
                    ],
                    "connections": [
                        {
                            "source_block_id": 0,
                            "sink_block_id": 1,
                            "criticality_q": 100,
                        }
                    ],
                },
                {
                    "net_id": 1,
                    "criticality_q": 1,
                    "pins": [
                        {"block_id": 0, "role": "source"},
                        {"block_id": 2, "role": "sink"},
                    ],
                    "connections": [
                        {
                            "source_block_id": 0,
                            "sink_block_id": 2,
                            "criticality_q": 1,
                        }
                    ],
                },
            ]
            make_contract(contract, blocks, sites, nets)
            input_place = root / "input.place"
            write_place(
                input_place,
                {
                    "netlist": "Netlist_File: synthetic.net Netlist_ID: SHA256:test",
                    "array_size": "Array size: 11 x 1 logic blocks",
                },
                [
                    {"name": "source", "x": 0, "y": 0, "subtile": 0, "layer": 0, "block_number": 0},
                    {"name": "critical_sink", "x": 1, "y": 0, "subtile": 0, "layer": 0, "block_number": 1},
                    {"name": "wire_sink", "x": 10, "y": 0, "subtile": 0, "layer": 0, "block_number": 2},
                ],
            )
            unguarded = tileplace_research.optimize(
                contract, input_place, root / "unguarded.place",
                4, 4, 1, 64, 256, 1, "connection_star", 0, 0, None, None, 1, False,
            )
            guarded = tileplace_research.optimize(
                contract, input_place, root / "guarded.place",
                4, 4, 1, 64, 256, 1, "connection_star", 100, 0, None, None, 1, False,
            )
            self.assertEqual(unguarded["accepted_moves"], 1)
            self.assertEqual(guarded["accepted_moves"], 0)
            self.assertGreater(guarded["rejected_guard_candidates"], 0)
            self.assertEqual(guarded["max_guarded_connection_delta"], 0)

    def test_connection_endpoints_map_to_clustered_blocks(self) -> None:
        blocks = [
            block(0, "source", 2),
            block(1, "sink_a", 5),
            block(2, "sink_b", 7),
        ]
        nets = [
            {
                "net_id": 0,
                "pins": [
                    {"block_id": 0, "role": "source", "path": "source"},
                    {"block_id": 1, "role": "sink", "path": "sink_a"},
                    {"block_id": 2, "role": "sink", "path": "sink_b"},
                ],
                "connections": [
                    {"source_rr_node": 10, "sink_rr_node": 11, "criticality_q": 100},
                    {"source_rr_node": 10, "sink_rr_node": 12, "criticality_q": 200},
                ],
            }
        ]
        summary = tileplace_vpr.annotate_connection_blocks(
            nets,
            blocks,
            {
                10: {"x": 2, "y": 0, "layer": 0, "ptc": 0},
                11: {"x": 5, "y": 0, "layer": 0, "ptc": 0},
                12: {"x": 7, "y": 0, "layer": 0, "ptc": 0},
            },
        )
        self.assertEqual(summary["timed_fully_mapped"], 2)
        self.assertEqual(nets[0]["connections"][0]["source_block_id"], 0)
        self.assertEqual(nets[0]["connections"][0]["sink_block_id"], 1)
        self.assertEqual(nets[0]["connections"][1]["sink_block_id"], 2)

    def test_io_sink_endpoint_uses_rr_class_to_disambiguate_subtile(self) -> None:
        blocks = [
            block(0, "source", 2),
            block(
                1, "out3", 0, logical_type="io",
                initial={"x": 0, "y": 0, "subtile": 3, "layer": 0},
            ),
            block(
                2, "out4", 0, logical_type="io",
                initial={"x": 0, "y": 0, "subtile": 4, "layer": 0},
            ),
        ]
        nets = [
            {
                "pins": [
                    {"block_id": 0, "role": "source"},
                    {"block_id": 1, "role": "sink"},
                    {"block_id": 2, "role": "sink"},
                ],
                "connections": [
                    {"source_rr_node": 10, "sink_rr_node": 11, "criticality_q": 100},
                    {"source_rr_node": 10, "sink_rr_node": 12, "criticality_q": 100},
                ],
            }
        ]
        summary = tileplace_vpr.annotate_connection_blocks(
            nets,
            blocks,
            {
                10: {"x": 2, "y": 0, "layer": 0, "ptc": 0},
                11: {"x": 0, "y": 0, "layer": 0, "ptc": 9},
                12: {"x": 0, "y": 0, "layer": 0, "ptc": 12},
            },
            {"1": {"name": "io", "capacity": 8, "class_count": 24}},
        )
        self.assertEqual(summary["timed_fully_mapped"], 2)
        self.assertEqual(nets[0]["connections"][0]["sink_block_id"], 1)
        self.assertEqual(nets[0]["connections"][1]["sink_block_id"], 2)

    def test_multitile_sink_endpoint_maps_to_root_clustered_block(self) -> None:
        blocks = [
            block(0, "source", 2),
            block(
                1, "dsp_sink", 9, logical_type="dsp_top",
                initial={"x": 9, "y": 4, "subtile": 0, "layer": 0},
            ),
        ]
        nets = [
            {
                "pins": [
                    {"block_id": 0, "role": "source"},
                    {"block_id": 1, "role": "sink"},
                ],
                "connections": [
                    {"source_rr_node": 10, "sink_rr_node": 11, "criticality_q": 100},
                ],
            }
        ]
        summary = tileplace_vpr.annotate_connection_blocks(
            nets,
            blocks,
            {
                10: {"x": 2, "y": 0, "layer": 0, "ptc": 0},
                11: {"x": 9, "y": 6, "layer": 0, "ptc": 41},
            },
            {
                "3": {
                    "name": "dsp_top", "capacity": 1, "class_count": 386,
                    "width": 1, "height": 4,
                }
            },
        )
        self.assertEqual(summary["timed_fully_mapped"], 1)
        self.assertEqual(nets[0]["connections"][0]["sink_block_id"], 1)

    def test_native_vpr_constraint_import_maps_atoms_to_clusters(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            packed = root / "design.net"
            packed.write_text(
                '<block name="design.net" instance="FPGA_packed_netlist[0]">\n'
                '  <block name="cluster0" instance="clb[0]">\n'
                '    <block name="atom_a" instance="lut[0]" />\n'
                '    <block name="atom_b" instance="ff[0]" />\n'
                '  </block>\n'
                '  <block name="out:pin" instance="io[0]">\n'
                '    <block name="out:pin" instance="outpad[0]" />\n'
                '  </block>\n'
                '</block>\n'
            )
            native = root / "constraints.xml"
            native.write_text(
                '<vpr_constraints tool_name="vpr"><partition_list>\n'
                '  <partition name="logic">\n'
                '    <add_atom name_pattern="atom_.*" />\n'
                '    <add_region x_low="1" y_low="2" x_high="3" y_high="4" />\n'
                '  </partition>\n'
                '  <partition name="fixed_io">\n'
                '    <add_atom name_pattern="out:pin" />\n'
                '    <add_region x_low="0" y_low="5" x_high="0" y_high="5" subtile="-1" />\n'
                '  </partition>\n'
                '</partition_list></vpr_constraints>\n'
            )
            constraints, summary = tileplace_vpr.parse_vpr_constraints(native, packed)
            self.assertEqual(summary["matched_atoms"], 3)
            self.assertEqual(summary["constrained_clusters"], 2)
            self.assertEqual(summary["coordinate_fixed_clusters"], 1)
            self.assertEqual(constraints["regions"]["cluster0"][0]["xmin"], 1)
            self.assertEqual(
                constraints["fixed_locations"]["out:pin"],
                {"x": 0, "y": 5, "subtile": None, "layer": 0},
            )

    def test_partial_fixed_location_keeps_subtile_free(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract = root / "contract"
            constrained = block(
                0,
                "fixed_xy",
                0,
                fixed=True,
                fixed_location={"x": 0, "y": 0, "subtile": None, "layer": 0},
                region=[
                    {
                        "xmin": 0,
                        "ymin": 0,
                        "xmax": 0,
                        "ymax": 0,
                        "layer_low": 0,
                        "layer_high": 0,
                        "subtile": -1,
                    }
                ],
            )
            sites = [site(0, 0), {**site(1, 0), "subtile": 1}, site(2, 1)]
            make_contract(contract, [constrained], sites)
            header = {
                "netlist": "Netlist_File: synthetic.net Netlist_ID: SHA256:test",
                "array_size": "Array size: 2 x 1 logic blocks",
            }
            legal = root / "legal.place"
            write_place(
                legal,
                header,
                [{"name": "fixed_xy", "x": 0, "y": 0, "subtile": 1, "layer": 0, "block_number": 0}],
            )
            self.assertTrue(tileplace_vpr.validate_contract(contract, legal)["legal"])
            illegal = root / "illegal.place"
            write_place(
                illegal,
                header,
                [{"name": "fixed_xy", "x": 1, "y": 0, "subtile": 0, "layer": 0, "block_number": 0}],
            )
            with self.assertRaisesRegex(tileplace_vpr.ContractError, "violates region"):
                tileplace_vpr.validate_contract(contract, illegal)

    def test_vpr_macro_echo_parser_and_orientation_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            placements = {
                "head": {"block_number": 0, "x": 3, "y": 4, "subtile": 0, "layer": 0},
                "tail": {"block_number": 1, "x": 3, "y": 3, "subtile": 0, "layer": 0},
            }
            echo = root / "place_macros.echo"
            echo.write_text(
                "#Identified Placement macros\n"
                "Num_Macros: 1\n"
                "Macro_Id: 0, Num_Blocks: 2\n"
                "Block_Id: 0 (head), x_offset: 0, y_offset: 0, z_offset: 0\n"
                "Block_Id: 1 (tail), x_offset: 0, y_offset: -1, z_offset: 0\n"
            )
            macros, summary = tileplace_vpr.parse_vpr_place_macros(echo, placements)
            self.assertEqual(summary["macro_count"], 1)
            self.assertEqual(summary["member_count"], 2)
            self.assertEqual(macros["tail"]["dy"], -1)
            self.assertEqual(macros["tail"]["source"], "vpr_direct")

            placements["tail"]["x"] = 4
            with self.assertRaisesRegex(tileplace_vpr.ContractError, "violates VPR macro"):
                tileplace_vpr.parse_vpr_place_macros(echo, placements)

    def test_unlimited_size_reference_exceeds_hls_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract = root / "contract"
            blocks = [block(index, f"b{index}", index) for index in range(600)]
            sites = [site(index, index) for index in range(600)]
            make_contract(contract, blocks, sites)
            output = root / "golden.place"
            report = tileplace_vpr.legalize(contract, output)
            self.assertEqual(report["blocks"], 600)
            self.assertEqual(report["moved_blocks"], 0)
            self.assertTrue(report["legal"])

    def test_fixed_region_macro_and_heterogeneous_sites(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract = root / "contract"
            blocks = [
                block(0, "fixed", 0, fixed=True),
                block(1, "region", 0, region=[1, 0, 1, 0]),
                block(2, "cascade0", 2, macro={"id": "cascade", "dx": 0, "dy": 0, "dsubtile": 0, "dlayer": 0}),
                block(3, "cascade1", 4, macro={"id": "cascade", "dx": 1, "dy": 0, "dsubtile": 0, "dlayer": 0}),
                block(4, "dsp", 6, logical_type="dsp"),
            ]
            sites = [site(index, index) for index in range(6)] + [site(6, 6, "dsp")]
            make_contract(contract, blocks, sites)
            output = root / "golden.place"
            report = tileplace_vpr.legalize(contract, output)
            self.assertTrue(report["legal"])
            self.assertEqual(report["macros"], 1)
            _header, rows = tileplace_vpr.parse_place(output)
            placed = {row["name"]: row for row in rows}
            self.assertEqual(placed["fixed"]["x"], 0)
            self.assertEqual(placed["region"]["x"], 1)
            self.assertEqual(placed["cascade1"]["x"] - placed["cascade0"]["x"], 1)
            self.assertEqual(placed["dsp"]["x"], 6)

    def test_validator_rejects_duplicate_occupancy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract = root / "contract"
            make_contract(contract, [block(0, "a", 0), block(1, "b", 1)], [site(0, 0), site(1, 1)])
            invalid = root / "invalid.place"
            invalid.write_text(
                "Netlist_File: synthetic.net Netlist_ID: SHA256:test\n"
                "Array size: 2 x 1 logic blocks\n\n"
                "#block name x y subblk layer block number\n"
                "a 0 0 0 0 #0\n"
                "b 0 0 0 0 #1\n"
            )
            with self.assertRaisesRegex(tileplace_vpr.ContractError, "already occupied"):
                tileplace_vpr.validate_contract(contract, invalid)

    def test_real_koios_contract_rejects_heterogeneous_corruption(self) -> None:
        project = Path(__file__).parents[1]
        contract = project / "experiments" / "koios_conv_layer_seed1_cw300"
        golden = contract / "conv_layer.pre-vpr.golden.place"
        if not golden.is_file():
            self.skipTest("real Koios contract is not present")
        blocks = tileplace_vpr.read_jsonl(contract / "blocks.jsonl")
        native_macros = {
            block["macro"]["id"]
            for block in blocks
            if (block.get("macro") or {}).get("source") == "vpr_direct"
        }
        self.assertEqual(len(native_macros), 43)
        header, original_rows = tileplace_vpr.parse_place(golden)
        by_name = {row["name"]: index for index, row in enumerate(original_rows)}
        clbs = [block for block in blocks if block["logical_type"] == "clb"]
        dsp = next(block for block in blocks if block["logical_type"] == "dsp_top")
        memory = next(block for block in blocks if block["logical_type"] == "memory")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)

            swapped = [dict(row) for row in original_rows]
            clb_row = swapped[by_name[clbs[0]["name"]]]
            dsp_row = swapped[by_name[dsp["name"]]]
            for field in ("x", "y", "subtile", "layer"):
                clb_row[field], dsp_row[field] = dsp_row[field], clb_row[field]
            swapped_path = root / "type_mismatch.place"
            write_place(swapped_path, header, swapped)
            with self.assertRaisesRegex(tileplace_vpr.ContractError, "incompatible"):
                tileplace_vpr.validate_contract(contract, swapped_path)

            duplicate = [dict(row) for row in original_rows]
            first = duplicate[by_name[clbs[0]["name"]]]
            second = duplicate[by_name[clbs[1]["name"]]]
            for field in ("x", "y", "subtile", "layer"):
                second[field] = first[field]
            duplicate_path = root / "duplicate.place"
            write_place(duplicate_path, header, duplicate)
            with self.assertRaisesRegex(tileplace_vpr.ContractError, "already occupied"):
                tileplace_vpr.validate_contract(contract, duplicate_path)
            recovered_path = root / "recovered.place"
            recovery = tileplace_vpr.legalize(contract, recovered_path, duplicate_path)
            self.assertTrue(recovery["legal"])
            self.assertGreater(recovery["moved_from_input"], 0)
            tileplace_vpr.validate_contract(contract, recovered_path)

            offset = [dict(row) for row in original_rows]
            memory_row = offset[by_name[memory["name"]]]
            memory_row["y"] += 1
            offset_path = root / "non_root_offset.place"
            write_place(offset_path, header, offset)
            with self.assertRaisesRegex(tileplace_vpr.ContractError, "not a root site"):
                tileplace_vpr.validate_contract(contract, offset_path)

            macro_members = [block for block in blocks if (block.get("macro") or {}).get("source") == "vpr_direct"]
            broken_macro = [dict(row) for row in original_rows]
            member_row = broken_macro[by_name[macro_members[1]["name"]]]
            member_row["x"] += 1
            broken_macro_path = root / "broken_macro.place"
            write_place(broken_macro_path, header, broken_macro)
            with self.assertRaisesRegex(tileplace_vpr.ContractError, "do not preserve"):
                tileplace_vpr.validate_contract(contract, broken_macro_path)


if __name__ == "__main__":
    unittest.main()
