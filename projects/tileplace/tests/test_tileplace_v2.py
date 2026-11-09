from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


TOOLS = Path(__file__).parents[1] / "tools"
for name in ("tileplace_vpr", "tileplace_v2", "prepare_route_feedback", "prepare_timing_feedback"):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

import tileplace_v2  # noqa: E402
import tileplace_vpr  # noqa: E402
import prepare_route_feedback  # noqa: E402
import prepare_timing_feedback  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def block(
    block_id: int,
    name: str,
    x: int,
    *,
    fixed: bool = False,
    macro: dict | None = None,
) -> dict:
    return {
        "block_id": block_id,
        "name": name,
        "logical_type": "clb",
        "mode": None,
        "initial": {"x": x, "y": 0, "subtile": 0, "layer": 0},
        "fixed": fixed,
        "region": None,
        "macro": macro,
    }


def site(site_id: int, x: int) -> dict:
    return {
        "site_id": site_id,
        "physical_type": "clb",
        "x": x,
        "y": 0,
        "subtile": 0,
        "layer": 0,
        "width": 1,
        "height": 1,
    }


def net(net_id: int, source: int, sink: int, criticality: int = 65535) -> dict:
    return {
        "net_id": net_id,
        "criticality_q": criticality,
        "pins": [
            {"block_id": source, "role": "source"},
            {"block_id": sink, "role": "sink"},
        ],
        "connections": [
            {
                "source_block_id": source,
                "sink_block_id": sink,
                "criticality_q": criticality,
            }
        ],
    }


def make_case(root: Path, blocks: list[dict], sites: list[dict], nets: list[dict]) -> tuple[Path, Path]:
    contract = root / "contract"
    contract.mkdir()
    outputs = {}
    for filename, rows in (("blocks.jsonl", blocks), ("sites.jsonl", sites), ("nets.jsonl", nets)):
        path = contract / filename
        path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows))
        outputs[filename] = {"count": len(rows), "sha256": digest(path)}
    header = {
        "netlist": "Netlist_File: synthetic.net Netlist_ID: SHA256:test",
        "array_size": "Array size: 16 x 1 logic blocks",
    }
    (contract / "manifest.json").write_text(
        json.dumps({"schema": tileplace_vpr.SCHEMA, "outputs": outputs, "placement_header": header})
    )
    place = root / "input.place"
    lines = [header["netlist"], header["array_size"], "", "#block name x y subblk layer block number"]
    for value in sorted(blocks, key=lambda row: row["block_id"]):
        lines.append(f"{value['name']} {value['initial']['x']} 0 0 0 #{value['block_id']}")
    place.write_text("\n".join(lines) + "\n")
    return contract, place


class TilePlaceV2Tests(unittest.TestCase):
    def test_ranked_timing_feedback_maps_and_collapses_cluster_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "timing.rpt"
            report.write_text(
                "#Path 1\n"
                "a.Q[0] (.latch) 0.1 0.1\n"
                "x.in[0] (.names) 0.1 0.2\n"
                "x.out[0] (.names) 0.1 0.3\n"
                "b.D[0] (.latch) 0.1 0.4\n"
                "#Path 2\n"
                "a.Q[0] (.latch) 0.1 0.1\n"
                "y.in[0] (.names) 0.1 0.2\n"
                "b.D[0] (.latch) 0.1 0.3\n"
            )
            edges, focus, count = prepare_timing_feedback.parse_ranked_edges(
                report, {"a": 1, "x": 2, "y": 2, "b": 3}, max_paths=2
            )
            self.assertEqual(count, 2)
            self.assertEqual(focus, {1, 2, 3})
            self.assertEqual(edges[(1, 2)], 65535 + 32767)
            self.assertEqual(edges[(2, 3)], 65535 + 32767)

    def test_ranked_timing_feedback_accepts_architecture_specific_io_ports(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "timing.rpt"
            report.write_text(
                "#Path 1\n"
                "clk.inpad[0] (.input) 0.0 0.0\n"
                "reg.q[0] (dffeas) 0.1 0.1\n"
                "out:result.outpad[0] (.output) 0.2 0.3\n"
            )
            edges, focus, count = prepare_timing_feedback.parse_ranked_edges(
                report, {"clk": 1, "reg": 2, "out:result": 3}, max_paths=1
            )
            self.assertEqual(count, 1)
            self.assertEqual(focus, {1, 2, 3})
            self.assertEqual(edges[(1, 2)], 65535)
            self.assertEqual(edges[(2, 3)], 65535)

    def test_route_feedback_uses_unique_node_per_net_and_capacity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            route = root / "test.route"
            route.write_text(
                "Net 0 (a)\nNode: 1 CHANX\nNode: 1 CHANX\nNode: 2 CHANY\n"
                "Net 1 (b)\nNode: 1 CHANX\n"
            )
            rr = root / "rr.xml"
            rr.write_text(
                '<rr_graph><rr_nodes>'
                '<node id="1" type="CHANX" capacity="1"><loc xlow="0" ylow="0" xhigh="2" yhigh="0"/></node>'
                '<node id="2" type="CHANY" capacity="2"><loc xlow="2" ylow="0" xhigh="2" yhigh="2"/></node>'
                '<node id="3" type="CHANX" capacity="1"><loc xlow="0" ylow="0" xhigh="2" yhigh="0"/></node>'
                '</rr_nodes></rr_graph>'
            )
            report = prepare_route_feedback.prepare(route, rr)
            by_edge = {
                (row["x0"], row["y0"], row["x1"], row["y1"]): row
                for row in report["edges"]
            }
            self.assertEqual(report["channel_node_uses"], 3)
            self.assertEqual(by_edge[(0, 0, 1, 0)]["occupancy"], 2)
            self.assertEqual(by_edge[(0, 0, 1, 0)]["capacity"], 2)
            self.assertEqual(by_edge[(0, 0, 1, 0)]["pressure_q16"], 1 << 16)
            self.assertEqual(by_edge[(2, 0, 2, 1)]["pressure_q16"], (1 << 16) // 4)

    def test_occupied_target_produces_improving_swap(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            blocks = [
                block(0, "a", 0),
                block(1, "b_sink", 1, fixed=True),
                block(2, "b", 3),
                block(3, "a_sink", 4, fixed=True),
            ]
            contract, place = make_case(
                root,
                blocks,
                [site(index, x) for index, x in enumerate((0, 1, 3, 4))],
                [net(0, 0, 3), net(1, 2, 1)],
            )
            engine = tileplace_v2.TilePlaceV2Engine(contract, place, tileplace_v2.V2Config())
            occupied = {loc: block_id for block_id, loc in engine.positions.items()}
            transactions = engine._transactions_for_unit((0,), occupied)
            swaps = [value for value in transactions if value.kind == "swap"]
            self.assertTrue(swaps)
            self.assertEqual(swaps[0].trial[0][0], 3)
            self.assertEqual(swaps[0].trial[2][0], 0)

    def test_chain3_is_generated_without_empty_sites(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            blocks = [
                block(0, "a", 0),
                block(1, "b", 1),
                block(2, "c", 2),
                block(3, "c_sink", 3, fixed=True),
                block(4, "b_sink", 4, fixed=True),
                block(5, "a_sink", 5, fixed=True),
            ]
            contract, place = make_case(
                root,
                blocks,
                [site(index, x) for index, x in enumerate(range(6))],
                [net(0, 0, 5, 65535), net(1, 1, 4, 65535), net(2, 2, 3, 1)],
            )
            engine = tileplace_v2.TilePlaceV2Engine(contract, place, tileplace_v2.V2Config())
            occupied = {loc: block_id for block_id, loc in engine.positions.items()}
            transactions = engine._transactions_for_unit((0,), occupied)
            self.assertTrue(any(value.kind == "chain3" for value in transactions))

    def test_shape_compatible_macros_swap_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            blocks = [
                block(0, "a0", 0, macro={"id": "a", "dx": 0, "dy": 0, "dsubtile": 0, "dlayer": 0}),
                block(1, "a1", 1, macro={"id": "a", "dx": 1, "dy": 0, "dsubtile": 0, "dlayer": 0}),
                block(2, "b0", 2, macro={"id": "b", "dx": 0, "dy": 0, "dsubtile": 0, "dlayer": 0}),
                block(3, "b1", 3, macro={"id": "b", "dx": 1, "dy": 0, "dsubtile": 0, "dlayer": 0}),
                block(4, "sink0", 4, fixed=True),
                block(5, "sink1", 5, fixed=True),
            ]
            contract, place = make_case(
                root,
                blocks,
                [site(index, x) for index, x in enumerate(range(6))],
                [net(0, 0, 4), net(1, 1, 5)],
            )
            engine = tileplace_v2.TilePlaceV2Engine(contract, place, tileplace_v2.V2Config())
            occupied = {loc: block_id for block_id, loc in engine.positions.items()}
            transactions = engine._transactions_for_unit((0, 1), occupied)
            macro_swaps = [value for value in transactions if value.kind == "macro_swap"]
            self.assertTrue(macro_swaps)
            self.assertEqual(set(macro_swaps[0].trial), {0, 1, 2, 3})

    def test_color_phase_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            blocks = [block(0, "a", 0), block(1, "b", 3), block(2, "sink", 4, fixed=True)]
            contract, place = make_case(
                root,
                blocks,
                [site(index, x) for index, x in enumerate((0, 1, 2, 3, 4))],
                [net(0, 0, 2), net(1, 1, 2)],
            )
            first = tileplace_v2.TilePlaceV2Engine(contract, place, tileplace_v2.V2Config())
            second = tileplace_v2.TilePlaceV2Engine(contract, place, tileplace_v2.V2Config())
            batch_a, audit_a = first.propose_color(0)
            batch_b, audit_b = second.propose_color(0)
            self.assertEqual([value.audit() for value in batch_a], [value.audit() for value in batch_b])
            self.assertEqual(audit_a, audit_b)


if __name__ == "__main__":
    unittest.main()
