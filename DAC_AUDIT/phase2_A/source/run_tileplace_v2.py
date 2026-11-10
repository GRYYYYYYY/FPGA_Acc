#!/usr/bin/env python3
"""Run TilePlace V2 with a bounded native VPR route/analysis oracle."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Iterable

from prepare_route_feedback import prepare as prepare_feedback
from prepare_timing_feedback import prepare as prepare_timing_feedback
from prepare_timing_feedback import parser_identity
from tileplace_provenance import (
    feedback_identity, file_snapshot, source_snapshot, verify_files, verify_implementation,
)
from tileplace_v2 import (
    TilePlaceV2Engine,
    Transaction,
    V2Config,
    load_feedback,
    load_timing_feedback,
)
from tileplace_vpr import ContractError, dump_json, sha256


Closure = dict[str, Any]
Oracle = Callable[[Path, Path, int], Closure]
FeedbackBuilder = Callable[[Closure], dict[tuple[int, int, int, int], int]]


class TimingRecorder:
    """Separate nondeterministic measurements from the search evidence report."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def call(self, stage: str, function: Callable, *args):
        start = time.perf_counter()
        succeeded = False
        try:
            result = function(*args)
            succeeded = True
            return result
        finally:
            self.events.append({"stage": stage, "wall_s": time.perf_counter() - start, "succeeded": succeeded})


def _metric(report: Closure, key: str) -> Decimal:
    if key not in report:
        raise ContractError(f"closure report is missing {key}")
    return Decimal(str(report[key]))


def acceptance_reason(candidate: Closure, incumbent: Closure, baseline: Closure) -> tuple[bool, str]:
    if candidate.get("status") != "pass" or candidate.get("legal") is not True:
        return False, "native_closure_not_legal"
    candidate_wl = int(candidate["wirelength"])
    baseline_wl = int(baseline["wirelength"])
    if candidate_wl * 1000 > baseline_wl * 1005:
        return False, "baseline_wirelength_cap_exceeded"
    candidate_cpd = _metric(candidate, "cpd_ns")
    incumbent_cpd = _metric(incumbent, "cpd_ns")
    if incumbent_cpd - candidate_cpd >= Decimal("0.001"):
        return True, "cpd_improved_at_least_1ps"
    if candidate_cpd == incumbent_cpd and candidate_wl < int(incumbent["wirelength"]):
        return True, "equal_cpd_wirelength_improved"
    return False, "timing_first_acceptance_not_met"


def _closure_summary(report: Closure) -> dict[str, Any]:
    return {
        key: report.get(key)
        for key in (
            "schema", "status", "legal", "wirelength", "cpd_ns", "returncode",
            "report_path", "report_sha256",
        )
        if key in report
    }


@dataclass
class SearchResult:
    report: dict[str, Any]
    incumbent: Closure


class RoutedSearch:
    """Deterministic batch trial, rollback, and stable bisection controller."""

    def __init__(
        self,
        engine: TilePlaceV2Engine,
        baseline: Closure,
        oracle: Oracle,
        feedback_builder: FeedbackBuilder,
        work: Path,
        max_closures: int = 24,
        epochs: int = 4,
        timings: TimingRecorder | None = None,
        use_no_goods: bool = True,
    ) -> None:
        if max_closures <= 0 or epochs <= 0:
            raise ContractError("closure budget and epoch count must be positive")
        if baseline.get("status") != "pass" or baseline.get("legal") is not True:
            raise ContractError("baseline closure must be legal and passing")
        _metric(baseline, "cpd_ns")
        int(baseline["wirelength"])
        self.engine = engine
        self.baseline = baseline
        self.incumbent = baseline
        self.oracle = oracle
        self.feedback_builder = feedback_builder
        self.work = work
        self.max_closures = max_closures
        self.epochs = epochs
        self.calls = 0
        self.accepted_transactions = 0
        self.trials: list[dict[str, Any]] = []
        self.phases: list[dict[str, Any]] = []
        self.rejected_singletons: set[tuple[Any, ...]] = set()
        self.timings = timings
        self.use_no_goods = use_no_goods

    def _measured(self, stage: str, function: Callable, *args):
        if self.timings is None:
            return function(*args)
        return self.timings.call(stage, function, *args)

    def _try(self, transactions: list[Transaction], epoch: int, color: int, depth: int) -> int:
        if not transactions or self.calls >= self.max_closures:
            return 0
        snapshot = self.engine.snapshot()
        trial_number = self.calls + 1
        trial_dir = self.work / f"trial_{trial_number:02d}"
        candidate_place = trial_dir / "candidate.place"
        trial_dir.mkdir(parents=True, exist_ok=True)
        self.engine.apply(transactions)
        self.engine.write_place(candidate_place)
        self.calls += 1
        before = _closure_summary(self.incumbent)
        try:
            closure = self._measured("oracle_driver", self.oracle, candidate_place, trial_dir, trial_number)
            accepted, reason = acceptance_reason(closure, self.incumbent, self.baseline)
        except Exception as error:  # A called oracle failure consumes one closure slot.
            closure = {"schema": "TILEPLACE_V2_ORACLE_FAILURE_V1", "status": "fail", "legal": False}
            accepted, reason = False, f"oracle_error:{type(error).__name__}:{error}"
        if accepted:
            pressure_before = dict(self.engine.pressure_q16)
            timing_before = (dict(self.engine.path_edges_q16), set(self.engine.focus_blocks)) if hasattr(self.engine, "path_edges_q16") else None
            try:
                feedback = self._measured("feedback_refresh", self.feedback_builder, closure)
                if isinstance(feedback, tuple):
                    pressure, timing = feedback
                    self.engine.update_timing_feedback(timing)
                    self.engine.pressure_q16 = pressure
                else:
                    self.engine.pressure_q16 = feedback
            except Exception as error:
                self.engine.pressure_q16 = pressure_before
                if timing_before is not None:
                    self.engine.path_edges_q16, self.engine.focus_blocks = timing_before
                accepted = False
                reason = f"feedback_error:{type(error).__name__}:{error}"
        audit = {
            "trial": trial_number,
            "epoch": epoch,
            "color": color,
            "bisection_depth": depth,
            "transaction_count": len(transactions),
            "transaction_ids": [repr(value.transaction_id) for value in transactions],
            "transactions": [value.audit() for value in transactions],
            "candidate_place": {"path": str(candidate_place.resolve()), "sha256": sha256(candidate_place)},
            "incumbent_before": before,
            "closure": _closure_summary(closure),
            "accepted": accepted,
            "reason": reason,
        }
        self.trials.append(audit)
        if accepted:
            self.incumbent = closure
            self.accepted_transactions += len(transactions)
            self.rejected_singletons.clear()
            return len(transactions)
        self.engine.restore(snapshot)
        if len(transactions) == 1:
            self.rejected_singletons.add(transactions[0].transaction_id)
            return 0
        if self.calls >= self.max_closures:
            return 0
        split = len(transactions) // 2
        accepted_count = self._try(transactions[:split], epoch, color, depth + 1)
        if self.calls < self.max_closures:
            accepted_count += self._try(transactions[split:], epoch, color, depth + 1)
        return accepted_count

    def run(self) -> SearchResult:
        stop_reason = "epoch_limit"
        completed_epochs = 0
        for epoch in range(self.epochs):
            epoch_accepted = 0
            epoch_proposals = 0
            forbidden_before = len(self.rejected_singletons)
            for color in range(4):
                if self.calls >= self.max_closures:
                    stop_reason = "closure_budget_exhausted"
                    break
                batch, phase = self._measured("proposal", self.engine.propose_color, color, self.rejected_singletons if self.use_no_goods else set())
                epoch_proposals += len(batch)
                phase.update({"epoch": epoch, "closure_calls_before": self.calls})
                accepted = self._try(batch, epoch, color, 0)
                phase.update({"oracle_accepted_transactions": accepted, "closure_calls_after": self.calls})
                self.phases.append(phase)
                epoch_accepted += accepted
            completed_epochs = epoch + 1
            if self.calls >= self.max_closures:
                stop_reason = "closure_budget_exhausted"
                break
            if epoch_proposals == 0:
                stop_reason = "candidate_frontier_exhausted"
                break
            if epoch_accepted == 0 and len(self.rejected_singletons) == forbidden_before:
                stop_reason = "candidate_frontier_stalled"
                break
        result = {
            "schema": "TILEPLACE_V2_ROUTED_SEARCH_V1",
            "status": "pass",
            "stop_reason": stop_reason,
            "epochs_completed": completed_epochs,
            "closure_budget": self.max_closures,
            "closure_calls": self.calls,
            "accepted_transactions": self.accepted_transactions,
            "final_rejected_singletons": len(self.rejected_singletons),
            "baseline": _closure_summary(self.baseline),
            "final": _closure_summary(self.incumbent),
            "phases": self.phases,
            "trials": self.trials,
        }
        return SearchResult(result, self.incumbent)


class NativeVprOracle:
    def __init__(self, args: argparse.Namespace, extra_vpr_args: Iterable[str]) -> None:
        self.args = args
        self.extra_vpr_args = list(extra_vpr_args)

    def __call__(self, candidate_place: Path, trial_dir: Path, trial_number: int) -> Closure:
        report_path = trial_dir / "vpr_native_closure.json"
        command = [
            sys.executable,
            str(Path(__file__).with_name("run_vpr_closure.py")),
            "--contract", str(self.args.contract.resolve()),
            "--vpr", str(self.args.vpr.resolve()),
            "--architecture", str(self.args.architecture.resolve()),
            "--circuit", str(self.args.circuit.resolve()),
            "--netlist", str(self.args.netlist.resolve()),
            "--golden-place", str(candidate_place.resolve()),
            "--work", str((trial_dir / "vpr").resolve()),
            "--report", str(report_path.resolve()),
            "--seed", str(self.args.seed),
            "--channel-width", str(self.args.channel_width),
        ]
        if self.args.max_router_iterations is not None:
            command.extend(["--max-router-iterations", str(self.args.max_router_iterations)])
        oracle_rr_graph = self.args.oracle_rr_graph or self.args.rr_graph
        if not self.args.rebuild_oracle_rr_graph:
            command.extend(["--", "--read_rr_graph", str(oracle_rr_graph.resolve())])
        command.extend(self.extra_vpr_args)
        process = subprocess.run(command, text=True, capture_output=True, check=False)
        (trial_dir / "oracle_driver.stdout.log").write_text(process.stdout)
        (trial_dir / "oracle_driver.stderr.log").write_text(process.stderr)
        if process.returncode != 0 or not report_path.is_file():
            return {
                "schema": "TILEPLACE_V2_ORACLE_FAILURE_V1",
                "status": "fail",
                "legal": False,
                "returncode": process.returncode,
            }
        report = json.loads(report_path.read_text())
        timing_report = trial_dir / "vpr" / "report_timing.setup.rpt"
        if not timing_report.is_file():
            raise ContractError("native closure did not produce report_timing.setup.rpt")
        report.setdefault("outputs", {})["timing_setup_report"] = {
            "path": str(timing_report.resolve()),
            "sha256": sha256(timing_report),
        }
        report["report_path"] = str(report_path.resolve())
        report["report_sha256"] = sha256(report_path)
        return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--input-place", type=Path, required=True)
    parser.add_argument("--baseline-closure", type=Path, required=True)
    parser.add_argument("--rr-graph", type=Path, required=True)
    parser.add_argument(
        "--oracle-rr-graph",
        type=Path,
        help="Equivalent serialized RR graph used only by native oracle closures",
    )
    parser.add_argument("--vpr", type=Path, required=True)
    parser.add_argument("--architecture", type=Path, required=True)
    parser.add_argument("--circuit", type=Path, required=True)
    parser.add_argument("--netlist", type=Path, required=True)
    parser.add_argument("--preregistration", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output-place", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--implementation-manifest", type=Path, help="Require exact source/parser identity before running")
    parser.add_argument("--timing-report", type=Path, help="Optional separate timing JSON; must be a new path, distinct from deterministic outputs")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--channel-width", type=int, required=True)
    parser.add_argument("--disable-no-goods", action="store_true", help="Ablation: retain rejection tracking and stopping rules but disable proposal suppression")
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--max-closures", type=int, default=24)
    parser.add_argument("--timing-weight", type=int, choices=(2, 4), default=2)
    parser.add_argument("--routed-timing-weight", type=int, default=0)
    parser.add_argument("--congestion-weight", type=int, choices=(0, 1), default=1)
    parser.add_argument("--critical-distance-guard-q", type=int, default=60000)
    parser.add_argument("--timing-feedback-paths", type=int, default=20)
    parser.add_argument("--max-router-iterations", type=int)
    parser.add_argument(
        "--rebuild-oracle-rr-graph",
        action="store_true",
        help="Rebuild the deterministic RR graph in each oracle closure instead of deserializing it",
    )
    parser.add_argument("extra_vpr_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    flow_start = time.perf_counter()
    timings = TimingRecorder() if args.timing_report is not None else None
    extra = args.extra_vpr_args[1:] if args.extra_vpr_args[:1] == ["--"] else args.extra_vpr_args
    try:
        tools_dir = Path(__file__).resolve().parent
        implementation = source_snapshot([
            tools_dir / name for name in (
                "run_tileplace_v2.py", "tileplace_v2.py", "tileplace_vpr.py",
                "prepare_route_feedback.py", "prepare_timing_feedback.py",
                "run_vpr_closure.py", "tileplace_provenance.py",
            )
        ], parser_identity())
        if implementation["parser"]["mode"] == "unregistered-regex":
            raise ContractError("production search requires the registered generic timing parser")
        if args.implementation_manifest is not None:
            verify_implementation(implementation, json.loads(args.implementation_manifest.read_text()))
        if args.timing_report is not None:
            timing_path = args.timing_report.resolve()
            if timing_path.exists() or timing_path in {args.report.resolve(), args.output_place.resolve()}:
                raise ContractError("timing report must be a new path distinct from output placement and report")
        if args.rebuild_oracle_rr_graph and args.oracle_rr_graph is not None:
            raise ContractError("choose either --rebuild-oracle-rr-graph or --oracle-rr-graph")
        if args.oracle_rr_graph is not None and not args.oracle_rr_graph.resolve().is_file():
            raise ContractError("oracle RR graph does not exist")
        prereg = json.loads(args.preregistration.resolve().read_text())
        if prereg.get("schema") != "TILEPLACE_V2_PREREGISTRATION_V1":
            raise ContractError("unsupported V2 preregistration schema")
        if sha256(args.vpr.resolve()) != prereg["oracle"]["vpr_sha256"]:
            raise ContractError("VPR binary does not match preregistration")
        if args.epochs != prereg["implementation"]["epochs"]:
            raise ContractError("epoch count differs from preregistration")
        registered_budget = prereg["oracle"].get(
            "maximum_route_analysis_closures_per_case_configuration",
            prereg["oracle"].get("maximum_route_analysis_closures_per_case"),
        )
        if registered_budget is None or args.max_closures > int(registered_budget):
            raise ContractError("closure budget exceeds preregistration")
        chosen = {
            "timing_weight": args.timing_weight,
            "routed_timing_weight": args.routed_timing_weight,
            "congestion_weight": args.congestion_weight,
            "critical_distance_guard_q": args.critical_distance_guard_q,
            "timing_feedback_paths": args.timing_feedback_paths,
        }
        registered = prereg["implementation"].get("development_configs")
        if registered is not None:
            if chosen not in registered:
                raise ContractError("configuration is not preregistered")
        else:
            legacy = {
                "timing_weight": args.timing_weight,
                "congestion_weight": args.congestion_weight,
            }
            if legacy not in prereg["implementation"]["development_weight_configs"]:
                raise ContractError("weight configuration is not preregistered")
            if args.routed_timing_weight != 0 or args.critical_distance_guard_q != 60000:
                raise ContractError("legacy preregistration does not permit routed timing feedback")
        baseline = json.loads(args.baseline_closure.resolve().read_text())
        baseline_route = Path(baseline["outputs"]["route"]["path"])
        contract_manifest = json.loads((args.contract.resolve() / "manifest.json").read_text())
        input_paths = [
            args.contract.resolve() / "manifest.json", args.input_place.resolve(),
            args.baseline_closure.resolve(), baseline_route, args.netlist.resolve(),
            args.rr_graph.resolve(), args.vpr.resolve(), args.architecture.resolve(),
            args.circuit.resolve(), args.preregistration.resolve(),
        ]
        input_paths.extend(args.contract.resolve() / name for name in contract_manifest["outputs"])
        input_paths.extend(Path(record["path"]) for record in contract_manifest["inputs"].values())
        if args.oracle_rr_graph is not None:
            input_paths.append(args.oracle_rr_graph.resolve())
        if args.routed_timing_weight > 0:
            input_paths.append(timing_report_for_closure(baseline))
        inputs = file_snapshot(input_paths)
        initial_feedback = prepare_feedback(baseline_route, args.rr_graph.resolve())
        timing_payload = None
        if args.routed_timing_weight > 0:
            timing_payload = prepare_timing_feedback(
                timing_report_for_closure(baseline),
                args.netlist.resolve(),
                args.contract.resolve() / "blocks.jsonl",
                args.timing_feedback_paths,
            )
        config = V2Config(
            timing_weight=args.timing_weight,
            routed_timing_weight=args.routed_timing_weight,
            congestion_weight=args.congestion_weight,
            critical_distance_guard_q=args.critical_distance_guard_q,
        )
        engine = TilePlaceV2Engine(
            args.contract.resolve(),
            args.input_place.resolve(),
            config,
            load_feedback_from_payload(initial_feedback),
            load_timing_feedback(timing_payload),
        )
        oracle = NativeVprOracle(args, extra)
        feedback_refreshes = []

        def feedback_builder(closure: Closure):
            route = Path(closure["outputs"]["route"]["path"])
            route_payload = prepare_feedback(route, args.rr_graph.resolve())
            pressure = load_feedback_from_payload(route_payload)
            if args.routed_timing_weight == 0:
                return pressure
            timing = prepare_timing_feedback(
                timing_report_for_closure(closure),
                args.netlist.resolve(),
                args.contract.resolve() / "blocks.jsonl",
                args.timing_feedback_paths,
            )
            feedback_refreshes.append({
                "candidate_route_sha256": route_payload["inputs"]["route"]["sha256"],
                "route_feedback_sha256": feedback_identity(route_payload),
                "timing_feedback_sha256": feedback_identity(timing),
                "timing_report_sha256": timing["inputs"]["timing_report"]["sha256"],
                "parser": timing["parser"],
            })
            return pressure, load_timing_feedback(timing)

        search = RoutedSearch(
            engine, baseline, oracle, feedback_builder, args.work.resolve(), args.max_closures, args.epochs,
            timings=timings, use_no_goods=not args.disable_no_goods,
        )
        search_start = time.perf_counter()
        result = search.run().report
        search_wall_s = time.perf_counter() - search_start
        engine.write_place(args.output_place.resolve())
        verify_files(implementation["sources"])
        verify_files(inputs)
        result.update(
            {
                "config": config.__dict__,
                "provenance": {
                    "schema": "TILEPLACE_SEARCH_PROVENANCE_V1",
                    "implementation": implementation,
                    "inputs": inputs,
                    "settings": {
                        "epochs": args.epochs, "max_closures": args.max_closures,
                        "use_no_goods": not args.disable_no_goods,
                        "timing_feedback_paths": args.timing_feedback_paths,
                        "rebuild_oracle_rr_graph": args.rebuild_oracle_rr_graph,
                        "extra_vpr_args": extra,
                    },
                    "initial_route_feedback_sha256": feedback_identity(initial_feedback),
                    "initial_timing_feedback_sha256": None if timing_payload is None else feedback_identity(timing_payload),
                    "feedback_refreshes": feedback_refreshes,
                    "source_and_input_hashes_unchanged_at_completion": True,
                },
                "preregistration": {
                    "path": str(args.preregistration.resolve()),
                    "sha256": sha256(args.preregistration.resolve()),
                },
                "input_place": {"path": str(args.input_place.resolve()), "sha256": sha256(args.input_place.resolve())},
                "output_place": {"path": str(args.output_place.resolve()), "sha256": sha256(args.output_place.resolve())},
                "initial_route_feedback": {
                    "route_sha256": initial_feedback["inputs"]["route"]["sha256"],
                    "rr_graph_sha256": initial_feedback["inputs"]["rr_graph"]["sha256"],
                    "edge_count": initial_feedback["edge_count"],
                },
                "initial_timing_feedback": None if timing_payload is None else {
                    "timing_report_sha256": timing_payload["inputs"]["timing_report"]["sha256"],
                    "parsed_paths": timing_payload["parsed_paths"],
                    "focus_blocks": len(timing_payload["focus_blocks"]),
                    "edge_count": len(timing_payload["edges"]),
                },
            }
        )
        dump_json(args.report.resolve(), result)
        if timings is not None:
            measured_end = time.perf_counter()
            totals = {
                stage: sum(event["wall_s"] for event in timings.events if event["stage"] == stage)
                for stage in ("proposal", "oracle_driver", "feedback_refresh")
            }
            dump_json(args.timing_report.resolve(), {
                "schema": "TILEPLACE_V4_FLOW_TIMING_V1",
                "status": "pass",
                "scope": "After CLI parsing through deterministic report write; excludes interpreter/import startup, precomputed inputs/baseline, timing JSON write and stdout",
                "flow_wall_s": measured_end - flow_start,
                "preparation_wall_s": search_start - flow_start,
                "search_wall_s": search_wall_s,
                "output_wall_s": measured_end - search_start - search_wall_s,
                "search_stage_wall_s": totals,
                "search_other_wall_s": search_wall_s - sum(totals.values()),
                "pressure_prefix": engine.pressure_prefix,
                "mechanism_profile": engine.profile,
                "events": timings.events,
                "report": {"path": str(args.report.resolve()), "sha256": sha256(args.report.resolve())},
                "limitations": "Single observation; externally time the command for full process wall time. oracle_driver includes validation, VPR, hashes and serialization; not just routing.",
            })
        print(json.dumps({key: value for key, value in result.items() if key not in {"phases", "trials"}}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"run_tileplace_v2: ERROR: {error}", file=sys.stderr)
        return 2


def load_feedback_from_payload(payload: dict[str, Any]) -> dict[tuple[int, int, int, int], int]:
    result: dict[tuple[int, int, int, int], int] = {}
    for row in payload.get("edges", []):
        key = (int(row["x0"]), int(row["y0"]), int(row["x1"]), int(row["y1"]))
        if key in result or int(row["pressure_q16"]) < 0:
            raise ContractError("invalid route-feedback payload")
        result[key] = int(row["pressure_q16"])
    return result


def timing_report_for_closure(closure: Closure) -> Path:
    timing = closure.get("outputs", {}).get("timing_setup_report", {}).get("path")
    if timing:
        path = Path(timing)
    else:
        path = Path(closure["outputs"]["stdout"]["path"]).parent / "report_timing.setup.rpt"
    if not path.is_file():
        raise ContractError(f"closure timing report does not exist: {path}")
    return path.resolve()


if __name__ == "__main__":
    raise SystemExit(main())
