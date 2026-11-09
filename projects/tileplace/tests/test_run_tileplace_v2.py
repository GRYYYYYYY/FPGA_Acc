from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


TOOLS = Path(__file__).parents[1] / "tools"
for name in (
    "tileplace_vpr", "tileplace_provenance", "prepare_route_feedback", "prepare_timing_feedback",
    "tileplace_v2", "run_tileplace_v2", "prepare_tileplace_v4_heldout_matrix",
):
    if name in sys.modules:
        continue
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

import run_tileplace_v2  # noqa: E402
import prepare_tileplace_v4_heldout_matrix as heldout_matrix  # noqa: E402
from tileplace_v2 import Transaction  # noqa: E402
from tileplace_vpr import ContractError, sha256  # noqa: E402


def transaction(number: int) -> Transaction:
    return Transaction(
        transaction_id=("mock", number),
        kind="move",
        units=((number,),),
        trial={number: (number, 0, 0, 0)},
        touched_nets=frozenset({number}),
        write_sites=frozenset({(number, 0, 0, 0)}),
        score_q20=-1,
        wire_delta=-1,
        timing_delta=-1,
        routed_timing_delta=-1,
        congestion_delta=0,
    )


def closure(cpd: float, wirelength: int, *, legal: bool = True) -> dict:
    return {
        "schema": "MOCK_CLOSURE_V1",
        "status": "pass" if legal else "fail",
        "legal": legal,
        "cpd_ns": cpd,
        "wirelength": wirelength,
    }


class FakeEngine:
    def __init__(self, batches: list[list[Transaction]]) -> None:
        self.state: list[int] = []
        self.batches = batches
        self.pressure_q16 = {}

    def snapshot(self) -> dict:
        return {index: value for index, value in enumerate(self.state)}

    def restore(self, snapshot: dict) -> None:
        self.state = [snapshot[index] for index in sorted(snapshot)]

    def apply(self, transactions: list[Transaction]) -> None:
        self.state.extend(int(value.transaction_id[1]) for value in transactions)

    def write_place(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(" ".join(str(value) for value in self.state) + "\n")

    def update_timing_feedback(self, feedback) -> None:
        self.timing_feedback = feedback

    def propose_color(self, color: int, _forbidden=None):
        batch = self.batches.pop(0) if self.batches else []
        return batch, {"color": color, "accepted": len(batch)}


class RoutedSearchTests(unittest.TestCase):
    def test_timing_preserves_report_and_counts_failed_oracle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            reports = []
            recorder = run_tileplace_v2.TimingRecorder()
            for timings in (None, recorder):
                engine = FakeEngine([[transaction(1)], [], [], [], [transaction(2)]])

                def oracle(_place, _work, trial):
                    if trial == 1:
                        raise ValueError("simulated oracle failure")
                    return closure(9.0, 1000)

                search = run_tileplace_v2.RoutedSearch(
                    engine, closure(10.0, 1000), oracle, lambda _: {},
                    Path(temporary), max_closures=2, epochs=2, timings=timings,
                )
                reports.append(search.run().report)
                self.assertEqual(engine.state, [2])
            self.assertEqual(reports[0], reports[1])
            oracle_events = [e for e in recorder.events if e["stage"] == "oracle_driver"]
            self.assertEqual([e["succeeded"] for e in oracle_events], [False, True])
            self.assertEqual(sum(e["stage"] == "feedback_refresh" for e in recorder.events), 1)
            self.assertTrue(all(e["wall_s"] >= 0 for e in recorder.events))

    def test_heldout_matrix_audits_final_accepted_state_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_place = root / "input.place"
            candidate_place = root / "candidate.place"
            output_place = root / "output.place"
            input_place.write_text("a 0 0 0 0 #0\n")
            candidate_place.write_text("a 1 0 0 0 #0\n")
            output_place.write_bytes(candidate_place.read_bytes())
            final = closure(9.9, 1001)
            report = {
                "closure_calls": 1,
                "accepted_transactions": 1,
                "input_place": {"path": str(input_place), "sha256": sha256(input_place)},
                "output_place": {"path": str(output_place), "sha256": sha256(output_place)},
                "baseline": closure(10.0, 1000),
                "final": final,
                "trials": [{
                    "trial": 1,
                    "transaction_count": 1,
                    "accepted": True,
                    "incumbent_before": closure(10.0, 1000),
                    "candidate_place": {
                        "path": str(candidate_place),
                        "sha256": sha256(candidate_place),
                    },
                    "closure": final,
                }],
            }
            heldout_matrix.verify_search_audit(report, "mock")
            # A rejected candidate must not become the next trial's incumbent,
            # even when the final accepted placement and metrics still match.
            import copy
            broken = copy.deepcopy(report)
            rejected = copy.deepcopy(broken["trials"][0])
            rejected.update(accepted=False, closure=closure(10.2, 1000))
            broken["trials"].insert(0, rejected)
            broken["trials"][1]["trial"] = 2
            broken["closure_calls"] = 2
            heldout_matrix.verify_search_audit(broken, "mock")
            broken["trials"][1]["incumbent_before"] = rejected["closure"]
            with self.assertRaisesRegex(ContractError, "incumbent state chain"):
                heldout_matrix.verify_search_audit(broken, "mock")
            report["output_place"]["sha256"] = "0" * 64
            with self.assertRaises(ContractError):
                heldout_matrix.verify_search_audit(report, "mock")

    def test_heldout_matrix_allows_only_semantic_reformat_for_zero_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_place = root / "input.place"
            output_place = root / "output.place"
            input_place.write_text("Netlist_File: mock.net\na 0 0 0 0 #0\n")
            output_place.write_text("# canonical output\na\t0\t0\t0\t0\t#0\n")
            baseline = closure(10.0, 1000)
            report = {
                "closure_calls": 0,
                "accepted_transactions": 0,
                "input_place": {"path": str(input_place), "sha256": sha256(input_place)},
                "output_place": {"path": str(output_place), "sha256": sha256(output_place)},
                "baseline": baseline,
                "final": baseline,
                "trials": [],
            }
            heldout_matrix.verify_search_audit(report, "mock")
            output_place.write_text("a 1 0 0 0 #0\n")
            report["output_place"]["sha256"] = sha256(output_place)
            with self.assertRaises(ContractError):
                heldout_matrix.verify_search_audit(report, "mock")

    def test_partial_feedback_update_restores_prior_timing_and_pressure(self):
        class BrokenFeedbackEngine(FakeEngine):
            def update_timing_feedback(self, feedback):
                self.path_edges_q16 = {(2, 3): 99}
                self.focus_blocks = {2}
                self.pressure_q16 = {(0, 0, 1, 0): 99}
                raise ValueError("partial refresh")
        with tempfile.TemporaryDirectory() as temporary:
            engine = BrokenFeedbackEngine([[transaction(1)]])
            engine.path_edges_q16 = {(0, 1): 7}
            engine.focus_blocks = {0}
            engine.pressure_q16 = {(0, 0, 1, 0): 7}
            search = run_tileplace_v2.RoutedSearch(
                engine, closure(10, 1000), lambda *_: closure(9, 1000),
                lambda _: ({}, ({(2, 3): 99}, {2})), Path(temporary),
                max_closures=1, epochs=1,
            )
            report = search.run().report
            self.assertFalse(report["trials"][0]["accepted"])
            self.assertEqual(engine.state, [])
            self.assertEqual(engine.path_edges_q16, {(0, 1): 7})
            self.assertEqual(engine.focus_blocks, {0})
            self.assertEqual(engine.pressure_q16, {(0, 0, 1, 0): 7})

    def test_no_good_ablation_changes_only_proposal_suppression(self) -> None:
        class FrontierEngine(FakeEngine):
            def propose_color(self, color, forbidden=None):
                if color != 0:
                    return [], {"color": color}
                candidate = transaction(2) if transaction(1).transaction_id in (forbidden or set()) else transaction(1)
                return [candidate], {"color": color}

        with tempfile.TemporaryDirectory() as temporary:
            for enabled in (True, False):
                engine = FrontierEngine([])
                seen = []
                def oracle(place, work, trial):
                    value = place.read_text().strip()
                    seen.append(value)
                    return closure(9.0 if value == "2" else 10.1, 1000)
                search = run_tileplace_v2.RoutedSearch(
                    engine, closure(10.0, 1000), oracle, lambda _: {},
                    Path(temporary), max_closures=2, epochs=2, use_no_goods=enabled,
                )
                report = search.run().report
                self.assertEqual(seen, ["1", "2"] if enabled else ["1", "1"])
                self.assertEqual(engine.state, [2] if enabled else [])
                self.assertEqual(report["closure_calls"], 2)
                self.assertEqual(report["accepted_transactions"], 1 if enabled else 0)

    def test_rejected_singleton_advances_to_next_epoch_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            engine = FakeEngine([[transaction(1)], [], [], [], [transaction(2)]])
            responses = iter([closure(10.1, 1000), closure(9.998, 1000)])
            search = run_tileplace_v2.RoutedSearch(
                engine, closure(10.0, 1000), lambda *_args: next(responses), lambda _value: {},
                Path(temporary), max_closures=2, epochs=2,
            )
            result = search.run().report
            self.assertEqual(result["closure_calls"], 2)
            self.assertEqual(engine.state, [2])
            self.assertEqual(result["accepted_transactions"], 1)

    def test_rejected_batch_is_rolled_back_and_bisected_stably(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            engine = FakeEngine([[transaction(1), transaction(2)]])
            responses = iter([closure(10.1, 1000), closure(9.998, 1000), closure(10.0, 999)])
            seen = []

            def oracle(place: Path, _work: Path, _trial: int) -> dict:
                seen.append(place.read_text().strip())
                return next(responses)

            search = run_tileplace_v2.RoutedSearch(
                engine, closure(10.0, 1000), oracle, lambda _value: {(0, 0, 1, 0): 7},
                Path(temporary), max_closures=3, epochs=1,
            )
            result = search.run().report
            self.assertEqual(seen, ["1 2", "1", "1 2"])
            self.assertEqual(engine.state, [1])
            self.assertEqual(result["closure_calls"], 3)
            self.assertEqual(result["accepted_transactions"], 1)
            self.assertEqual(engine.pressure_q16, {(0, 0, 1, 0): 7})

    def test_budget_exhaustion_prevents_second_half_trial(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            engine = FakeEngine([[transaction(1), transaction(2)]])
            calls = []

            def oracle(place: Path, _work: Path, trial: int) -> dict:
                calls.append((trial, place.read_text().strip()))
                return closure(10.1, 1000)

            search = run_tileplace_v2.RoutedSearch(
                engine, closure(10.0, 1000), oracle, lambda _value: {}, Path(temporary),
                max_closures=2, epochs=1,
            )
            result = search.run().report
            self.assertEqual(calls, [(1, "1 2"), (2, "1")])
            self.assertEqual(engine.state, [])
            self.assertEqual(result["stop_reason"], "closure_budget_exhausted")

    def test_equal_cpd_requires_strict_wirelength_improvement(self) -> None:
        baseline = closure(10.0, 1000)
        self.assertEqual(
            run_tileplace_v2.acceptance_reason(closure(10.0, 999), baseline, baseline),
            (True, "equal_cpd_wirelength_improved"),
        )
        self.assertFalse(run_tileplace_v2.acceptance_reason(closure(10.0, 1000), baseline, baseline)[0])

    def test_wirelength_cap_and_feedback_failure_are_fail_closed(self) -> None:
        baseline = closure(10.0, 1000)
        self.assertTrue(run_tileplace_v2.acceptance_reason(closure(9.0, 1005), baseline, baseline)[0])
        self.assertEqual(
            run_tileplace_v2.acceptance_reason(closure(9.0, 1006), baseline, baseline)[1],
            "baseline_wirelength_cap_exceeded",
        )
        with tempfile.TemporaryDirectory() as temporary:
            engine = FakeEngine([[transaction(1)]])

            def broken_feedback(_closure: dict) -> dict:
                raise ValueError("bad route")

            search = run_tileplace_v2.RoutedSearch(
                engine, baseline, lambda *_args: closure(9.0, 1000), broken_feedback,
                Path(temporary), max_closures=1, epochs=1,
            )
            result = search.run().report
            self.assertEqual(engine.state, [])
            self.assertFalse(result["trials"][0]["accepted"])
            self.assertTrue(result["trials"][0]["reason"].startswith("feedback_error:"))


if __name__ == "__main__":
    unittest.main()
