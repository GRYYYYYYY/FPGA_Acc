#!/usr/bin/env python3
"""Generate a paired frontier table only from completed, bound audit evidence."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from audit_frontier_ablation import PROTOCOL_SHA
from tileplace_vpr import ContractError, sha256


def main():
    paper = Path(__file__).resolve().parent
    exp = paper.parent / "experiments"
    audit_path = exp / "tileplace_frontier_ablation_audit_2026-09-29.json"
    audit = json.loads(audit_path.read_text())
    matrix = exp / "tileplace_frontier_ablation_2026-09-29" / "summary.json"
    protocol = exp / "tileplace_frontier_ablation_protocol_2026-09-29.json"
    if (audit.get("status") != "pass" or audit.get("schema") != "TILEPLACE_FRONTIER_PAIRED_AUDIT_V1"
            or audit.get("protocol_sha256") != PROTOCOL_SHA or sha256(protocol) != PROTOCOL_SHA
            or sha256(matrix) != audit.get("matrix_sha256")):
        raise ContractError("completed bound paired audit required")
    rows = audit["pairs"]
    names = [r["design"] for r in rows]
    if len(names) != 4 or set(names) != {"diffeq", "frisc", "elliptic", "clma"}:
        raise ContractError("four unique paired designs required")
    lines = ["% Enabled / disabled; negative changes favor enabled suppression.",
             "% Audit SHA256: " + sha256(audit_path),
             r"\begin{tabular}{lrrrr}", r"\toprule",
             r"Case & $\Delta$CPD (\%) & $\Delta$WL (\%) & Calls on/off & Accepts on/off \\",
             r"\midrule"]
    for row in rows:
        on, off = row["enabled"], row["disabled"]
        lines.append(f"{row['design']} & {100 * (row['cpd_enabled_over_disabled'] - 1):+.3f} & "
                     f"{100 * (row['wirelength_enabled_over_disabled'] - 1):+.3f} & "
                     f"{on['closure_calls']}/{off['closure_calls']} & "
                     f"{on['accepted_transactions']}/{off['accepted_transactions']} " + r"\\")
    lines.extend([r"\midrule", f"Geo. mean & {audit['cpd_paired_geomean_change_pct']:+.3f} & "
                  f"{audit['wirelength_paired_geomean_change_pct']:+.3f} & --- & --- " + r"\\",
                  r"\bottomrule", r"\end{tabular}"])
    output = paper / "generated" / "frontier_ablation_table.tex"
    output.write_text("\n".join(lines) + "\n")
    print(output)


if __name__ == "__main__":
    main()
