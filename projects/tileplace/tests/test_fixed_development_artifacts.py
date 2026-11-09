"""Legal flags must not hide a wrong candidate binding or missing VPR success."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))
from audit_fixed_development import audit_native_trials
from tileplace_vpr import ContractError, sha256


class NativeArtifactTests(unittest.TestCase):
    def test_candidate_binding_and_success_log_are_independently_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / "candidate.place"
            candidate.write_text("a 0 0 0 0 #0\n")
            stdout = root / "stdout.log"
            markers = ["Completed placement consistency check successfully.",
                       "Completed routing consistency check successfully.",
                       "Circuit successfully routed with a channel width factor 200", "VPR succeeded"]
            stdout.write_text("\n".join(markers))
            native = {"schema": "native", "status": "pass", "legal": True, "returncode": 0,
                      "wirelength": 100, "cpd_ns": 10,
                      "inputs": {"golden_place": {"sha256": sha256(candidate)}},
                      "outputs": {"stdout": {"path": str(stdout), "sha256": sha256(stdout)}}}
            path = root / "closure.json"

            def report():
                path.write_text(json.dumps(native))
                summary = {k: native[k] for k in ("schema", "status", "legal", "returncode", "wirelength", "cpd_ns")}
                summary.update(report_path=str(path), report_sha256=sha256(path))
                return {"trials": [{"candidate_place": {"path": str(candidate), "sha256": sha256(candidate)}, "closure": summary}]}

            self.assertEqual(audit_native_trials(report()), 1)
            native["inputs"]["golden_place"]["sha256"] = "0" * 64
            with self.assertRaisesRegex(ContractError, "different candidate"):
                audit_native_trials(report())
            native["inputs"]["golden_place"]["sha256"] = sha256(candidate)
            stdout.write_text("\n".join(markers[:-1]))
            native["outputs"]["stdout"]["sha256"] = sha256(stdout)
            with self.assertRaisesRegex(ContractError, "success marker missing"):
                audit_native_trials(report())


if __name__ == "__main__":
    unittest.main()
