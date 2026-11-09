#!/usr/bin/env python3
"""Validate frozen TilePlace evidence and emit paper-ready LaTeX fragments."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


PAPER_DIR = Path(__file__).resolve().parent
EXPERIMENTS = PAPER_DIR.parent / "experiments"
GENERATED = PAPER_DIR / "generated"

INPUTS = {
    "v4": (
        "tileplace_v4_heldout_matrix_2026-09-05.json",
        "744a02558869acc6baafbced927f3bf16fdd12690bcd08bce00d0accd22498cf",
    ),
    "qor": (
        "timing_titan_stereo_extended_matrix_2026-09-02.json",
        "0c40eb7fbb0e1616d9b31b0310a2baacea1c1d8a588166a1cf96bc0da2558873",
    ),
    "constrained": (
        "constrained_qor_matrix_2026-09-01.json",
        "49a39a6ef45fc09b42386ae3894fb3a0c00ef67bb40b5722ff27f0300797bea4",
    ),
    "baseline": ("vpr_placement_baseline_matrix_2026-08-31.json", None),
    "pages": ("page_size_ablation_2026-08-31.json", None),
    "runtime": ("cpu_runtime_sixcase_matrix_2026-08-31.json", None),
    "guard_runtime": ("runtime_guard_elision_ablation_2026-08-31.json", None),
}


def load(name: str) -> dict:
    filename, expected_sha = INPUTS[name]
    path = EXPERIMENTS / filename
    payload = path.read_bytes()
    actual_sha = hashlib.sha256(payload).hexdigest()
    if expected_sha is not None and actual_sha != expected_sha:
        raise SystemExit(f"frozen evidence hash mismatch: {path}: {actual_sha}")
    return json.loads(payload)


def close(actual: float, expected: float, tolerance: float = 5e-4) -> None:
    if abs(actual - expected) > tolerance:
        raise AssertionError(f"expected {expected}, found {actual}")


def pct(value: float) -> str:
    if abs(value) < 0.0005:
        return "0.000"
    return f"{value:+.3f}"


def tex_name(name: str) -> str:
    labels = {
        "attention_layer": r"attention\_layer",
        "conv_layer": r"conv\_layer$^{\dagger}$",
        "titan23_neuron": r"Titan23 neuron",
        "titan23_stereo_vision": r"Titan23 stereo",
        "tdarknet_like.small": r"tdarknet\_like.small",
    }
    return labels.get(name, name.replace("_", r"\_"))


def write(name: str, text: str) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / name).write_text(text.rstrip() + "\n")


def validate(v4: dict, qor: dict, constrained: dict, baseline: dict) -> None:
    assert v4["schema"] == "TILEPLACE_V4_HELDOUT_MATRIX_V1"
    assert v4["status"] == "pass"
    assert v4["preregistration"]["sha256"] == (
        "75dce71634d613f17db59a0af923d258cf5b95fe795566a37596486656cfa3ca"
    )
    assert v4["audit"] == {
        "all_reports_within_closure_budget": True,
        "all_trial_state_chains_verified": True,
        "frozen_closure_budget": 24,
        "frozen_configuration_verified": True,
    }
    assert {case["case"] for case in v4["cases"]} == {
        "pdc", "dsip", "bnn", "gemm_layer", "tdarknet_like.small", "ucsb_152_tap_fir",
    }
    va = v4["aggregate"]
    assert va["cases"] == 6 and va["strict_cpd_improvements"] == 3
    close(va["cpd_geomean_change_pct"], -5.049)
    close(va["wirelength_geomean_change_pct"], -0.507)
    close((va["maximum_wirelength_ratio"] - 1.0) * 100.0, 0.270)
    assert all(v4["publication_gate"].values())
    tdarknet = next(case for case in v4["cases"] if case["case"] == "tdarknet_like.small")
    close(tdarknet["cpd_change_pct"], -21.289)
    close(tdarknet["wirelength_change_pct"], 0.270)
    assert tdarknet["closure_calls"] == 20 and tdarknet["accepted_transactions"] == 8

    assert qor["status"] == "pass"
    assert qor["aggregate"]["cases"] == 10
    assert len(qor["cases"]) == 10
    assert qor["endpoint_mapping"]["connections"] == 280205
    assert qor["endpoint_mapping"]["mapped_sources"] == 280205
    assert qor["endpoint_mapping"]["mapped_sinks"] == 280205
    assert qor["atom_timing_pin_mapping"]["mapped"] == 275654
    assert qor["atom_timing_pin_mapping"]["unmapped"] == 4551
    close(qor["aggregate"]["wirelength_geomean_delta_pct"], -0.066)
    close(qor["aggregate"]["cpd_geomean_delta_pct"], -0.911)
    assert qor["aggregate"]["wirelength_improved_cases"] == 5
    assert qor["aggregate"]["cpd_nonregressing_cases"] == 9

    cases = {case["case"]: case for case in qor["cases"]}
    assert set(cases) == {
        "diffeq",
        "frisc",
        "elliptic",
        "clma",
        "spmv",
        "softmax",
        "attention_layer",
        "conv_layer",
        "titan23_neuron",
        "titan23_stereo_vision",
    }
    assert sum(case["cohort"] == "development" for case in cases.values()) == 4
    assert sum(case["cohort"] == "post_freeze_validation" for case in cases.values()) == 5
    assert cases["conv_layer"]["cohort"] == "macro_stress_previously_probed"
    post = qor["cohort_aggregates"]["post_freeze_validation"]
    assert post["cases"] == 5 and post["cpd_nonregressing_cases"] == 5
    close(post["wirelength_geomean_delta_pct"], 0.015)
    close(post["cpd_geomean_delta_pct"], -1.797)

    conv = cases["conv_layer"]
    assert conv["endpoint_mapping"]["atom_timing_pin_unmapped"] == 4440
    assert conv["macros"]["macro_count"] == 43
    assert conv["macros"]["member_count"] == 86
    neuron = cases["titan23_neuron"]
    assert neuron["endpoint_mapping"]["atom_timing_pin_unmapped"] == 0
    assert neuron["macros"]["macro_count"] == 101
    assert neuron["macros"]["member_count"] == 204
    stereo = cases["titan23_stereo_vision"]
    assert stereo["endpoint_mapping"]["connections"] == 81610
    assert stereo["endpoint_mapping"]["atom_timing_pin_mapped"] == 81499
    assert stereo["endpoint_mapping"]["atom_timing_pin_unmapped"] == 111
    assert stereo["macros"]["macro_count"] == 150
    assert stereo["macros"]["member_count"] == 300
    close(stereo["candidate"]["wirelength_delta_pct"], 0.135)
    close(stereo["candidate"]["cpd_delta_pct"], -0.020)

    assert constrained["status"] == "pass"
    assert constrained["constraints"]["fixed_clusters_preserved"] == 28
    assert constrained["endpoint_mapping"]["atom_timing_pin_mapped"] == 2263
    assert constrained["separate_from"] == [
        "nine-case unconstrained TilePlace QoR aggregate",
        "six-case Eigen conventional/AP aggregate",
    ]
    close(constrained["candidate"]["wirelength_delta_pct"], 0.210, 1e-3)
    close(constrained["candidate"]["cpd_delta_pct"], 0.463, 1e-3)

    assert baseline["status"] == "pass"
    assert len(baseline["cases"]) == 6
    for case in baseline["cases"]:
        assert case["same_packed_netlist"] and case["same_router"]
        assert case["conventional"]["moved_from_reference"] == 0
    analytic = baseline["aggregate"]["analytic_vs_conventional"]
    close(analytic["wirelength_geomean_delta_pct"], 3.711)
    close(analytic["cpd_geomean_delta_pct"], 16.103)


def emit_qor_table(qor: dict) -> None:
    lines = [
        r"\begin{tabular}{lrrrrr}",
        r"\toprule",
        r"Case & Base WL & $\Delta$WL (\%) & Base CPD & $\Delta$CPD (\%) & Iters \\",
        r"\midrule",
    ]
    for case in qor["cases"]:
        b, c = case["baseline"], case["candidate"]
        lines.append(
            f"{tex_name(case['case'])} & {b['wirelength']} & {pct(c['wirelength_delta_pct'])} & "
            f"{b['cpd_ns']:.5g} & {pct(c['cpd_delta_pct'])} & "
            f"{b['routing_iterations']}--{c['routing_iterations']} \\\\" 
        )
    aggregate = qor["aggregate"]
    lines.extend(
        [
            r"\midrule",
            f"Geomean & -- & \\textbf{{{pct(aggregate['wirelength_geomean_delta_pct'])}}} & -- & "
            f"\\textbf{{{pct(aggregate['cpd_geomean_delta_pct'])}}} & -- \\\\",
            r"\bottomrule",
            r"\end{tabular}",
        ]
    )
    write("qor_table.tex", "\n".join(lines))


def emit_v4_table(v4: dict) -> None:
    lines = [
        r"\begin{tabular}{lrrrrrr}",
        r"\toprule",
        r"Case & Base WL & $\Delta$WL (\%) & Base CPD & $\Delta$CPD (\%) & Closures & Accepts \\",
        r"\midrule",
    ]
    for case in v4["cases"]:
        lines.append(
            f"{tex_name(case['case'])} & {case['baseline_wirelength']} & "
            f"{pct(case['wirelength_change_pct'])} & {case['baseline_cpd_ns']:.5g} & "
            f"{pct(case['cpd_change_pct'])} & {case['closure_calls']} & "
            f"{case['accepted_transactions']} \\\\" 
        )
    aggregate = v4["aggregate"]
    lines.extend(
        [
            r"\midrule",
            f"Geomean & -- & \\textbf{{{pct(aggregate['wirelength_geomean_change_pct'])}}} & -- & "
            f"\\textbf{{{pct(aggregate['cpd_geomean_change_pct'])}}} & -- & -- \\\\",
            r"\bottomrule",
            r"\end{tabular}",
        ]
    )
    write("v4_table.tex", "\n".join(lines))


def emit_baseline_table(baseline: dict) -> None:
    lines = [
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"Case & TilePlace $\Delta$WL & TilePlace $\Delta$CPD & AP $\Delta$WL & AP $\Delta$CPD \\",
        r"\midrule",
    ]
    for case in baseline["cases"]:
        t, a = case["tileplace"], case["analytic"]
        lines.append(
            f"{tex_name(case['case'])} & {pct(t['wirelength_delta_pct'])} & {pct(t['cpd_delta_pct'])} & "
            f"{pct(a['wirelength_delta_pct'])} & {pct(a['cpd_delta_pct'])} \\\\" 
        )
    aggregate = baseline["aggregate"]
    t = aggregate["tileplace_vs_conventional"]
    a = aggregate["analytic_vs_conventional"]
    lines.extend(
        [
            r"\midrule",
            f"Geomean & \\textbf{{{pct(t['wirelength_geomean_delta_pct'])}}} & "
            f"\\textbf{{{pct(t['cpd_geomean_delta_pct'])}}} & "
            f"{pct(a['wirelength_geomean_delta_pct'])} & {pct(a['cpd_geomean_delta_pct'])} \\\\",
            r"\bottomrule",
            r"\end{tabular}",
        ]
    )
    write("baseline_table.tex", "\n".join(lines))


def emit_runtime_table(runtime: dict) -> None:
    lines = [
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        r"Case & Blocks & Timed connections & Median wall (s) \\",
        r"\midrule",
    ]
    for case in runtime["cases"]:
        lines.append(
            f"{tex_name(case['case'])} & {case['blocks']} & {case['timed_connections']} & "
            f"{case['wall_s']['median']:.3f} \\\\" 
        )
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    write("runtime_table.tex", "\n".join(lines))


def emit_page_table(pages: dict) -> None:
    lines = [
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        r"Page & WL geomean (\%) & Worst WL (\%) & CPD geomean (\%) \\",
        r"\midrule",
    ]
    for row in pages["sizes"]:
        a = row["aggregate"]
        page = rf"{row['page_size'][0]}$\times${row['page_size'][1]}"
        selected = row["page_size"] == pages["selected_page_size"]
        values = (
            page,
            pct(a["wirelength_geomean_delta_pct"]),
            pct(a["wirelength_worst_delta_pct"]),
            pct(a["cpd_geomean_delta_pct"]),
        )
        text = " & ".join(rf"\textbf{{{value}}}" for value in values) if selected else " & ".join(values)
        lines.append(text + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    write("page_table.tex", "\n".join(lines))


def emit_cohort_table(qor: dict) -> None:
    cohort_labels = {
        "development": "Development",
        "post_freeze_validation": "Post-freeze",
        "macro_stress_previously_probed": "Macro stress",
    }
    lines = [
        r"\begin{tabular}{llrr}",
        r"\toprule",
        r"Case & Cohort & Connections & Macros/members \\",
        r"\midrule",
    ]
    for case in qor["cases"]:
        macros = case.get("macros")
        macro_text = "--" if macros is None else f"{macros['macro_count']}/{macros['member_count']}"
        lines.append(
            f"{tex_name(case['case'])} & {cohort_labels[case['cohort']]} & "
            f"{case['endpoint_mapping']['connections']} & {macro_text} \\\\" 
        )
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    write("cohort_table.tex", "\n".join(lines))


def emit_macros(v4: dict, qor: dict, constrained: dict, baseline: dict, guard_runtime: dict) -> None:
    va = v4["aggregate"]
    qa = qor["aggregate"]
    post = qor["cohort_aggregates"]["post_freeze_validation"]
    analytic = baseline["aggregate"]["analytic_vs_conventional"]
    definitions = {
        "VFourWlGeo": pct(va["wirelength_geomean_change_pct"]),
        "VFourCpdGeo": pct(va["cpd_geomean_change_pct"]),
        "VFourStrict": va["strict_cpd_improvements"],
        "VFourWorstWl": pct((va["maximum_wirelength_ratio"] - 1.0) * 100.0),
        "QorCases": qa["cases"],
        "QorWlGeo": pct(qa["wirelength_geomean_delta_pct"]),
        "QorCpdGeo": pct(qa["cpd_geomean_delta_pct"]),
        "PostFreezeWlGeo": pct(post["wirelength_geomean_delta_pct"]),
        "PostFreezeCpdGeo": pct(post["cpd_geomean_delta_pct"]),
        "MappedConnections": qor["endpoint_mapping"]["connections"],
        "MappedAtomPins": qor["atom_timing_pin_mapping"]["mapped"],
        "UnmappedAtomPins": qor["atom_timing_pin_mapping"]["unmapped"],
        "FixedIoClusters": constrained["constraints"]["fixed_clusters_preserved"],
        "ConstrainedWl": pct(constrained["candidate"]["wirelength_delta_pct"]),
        "ConstrainedCpd": pct(constrained["candidate"]["cpd_delta_pct"]),
        "ApWlGeo": pct(analytic["wirelength_geomean_delta_pct"]),
        "ApCpdGeo": pct(analytic["cpd_geomean_delta_pct"]),
        "GuardRuntimeSpeedup": f"{guard_runtime['aggregate']['geomean_speedup']:.3f}",
    }
    write(
        "summary_macros.tex",
        "\n".join(rf"\newcommand{{\{key}}}{{{value}}}" for key, value in definitions.items()),
    )


def main() -> None:
    data = {name: load(name) for name in INPUTS}
    validate(data["v4"], data["qor"], data["constrained"], data["baseline"])
    emit_v4_table(data["v4"])
    emit_qor_table(data["qor"])
    emit_baseline_table(data["baseline"])
    emit_runtime_table(data["runtime"])
    emit_page_table(data["pages"])
    emit_cohort_table(data["qor"])
    emit_macros(
        data["v4"], data["qor"], data["constrained"], data["baseline"], data["guard_runtime"]
    )
    emit_fixed_development_if_audited()
    print(f"validated {len(INPUTS)} frozen evidence files; wrote {len(list(GENERATED.glob('*.tex')))} LaTeX fragments")


def emit_fixed_development_if_audited() -> None:
    audit_path = EXPERIMENTS / "tileplace_fixed_development_audit_2026-09-29.json"
    if not audit_path.exists():
        if (GENERATED / "fixed_development_table.tex").exists():
            raise SystemExit("fixed-development table exists without its completed artifact audit")
        return
    audit = json.loads(audit_path.read_text())
    if audit.get("status") != "pass" or audit.get("implementation_sha256") != (
        "0f8a684ae7dc745fceb257d62a71bd8f34f61bf41db5cc515dfb641b6557d2a3"
    ):
        raise SystemExit("fixed-development audit is incomplete or uses another implementation")
    matrix_path = Path(audit["matrix"]["path"])
    payload = matrix_path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != audit["matrix"]["sha256"]:
        raise SystemExit("fixed-development matrix changed after artifact audit")
    matrix = json.loads(payload)
    expected = {"diffeq", "frisc", "elliptic", "clma"}
    if {r["case"] for r in matrix["cases"]} != expected or len(matrix["cases"]) != 4:
        raise SystemExit("fixed-development cohort is not exactly the four registered designs")
    if {r["case"] for r in audit["cases"]} != expected or not all(r["all_repeats_exact"] for r in audit["cases"]):
        raise SystemExit("fixed-development audit does not cover exact four-case repeats")
    lines = [r"\begin{tabular}{lrrrrr}", r"\toprule",
             r"Case & Base CPD & Final CPD & $\Delta$CPD (\%) & $\Delta$WL (\%) & Repeats \\", r"\midrule"]
    for row in matrix["cases"]:
        lines.append(
            f"{tex_name(row['case'])} & {row['baseline']['cpd_ns']:.5g} & {row['final']['cpd_ns']:.5g} & "
            f"{pct((row['cpd_ratio'] - 1) * 100)} & {pct((row['wirelength_ratio'] - 1) * 100)} & "
            f"{row['repeat_count']} \\\\"
        )
    lines += [r"\midrule",
              f"Geomean & -- & -- & {pct(matrix['cpd_geomean_change_pct'])} & "
              f"{pct(matrix['wirelength_geomean_change_pct'])} & -- \\\\",
              r"\bottomrule", r"\end{tabular}"]
    write("fixed_development_table.tex", "\n".join(lines))


if __name__ == "__main__":
    main()
