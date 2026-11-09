"""Partial or stale development evidence must not become a paper table."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("tileplace_paper_artifacts", Path(__file__).parents[1] / "paper/prepare_artifacts.py")
artifacts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(artifacts)


class FixedPaperArtifactTests(unittest.TestCase):
    def test_partial_missing_and_changed_evidence_reject_table(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = artifacts.EXPERIMENTS, artifacts.GENERATED
            artifacts.EXPERIMENTS = artifacts.GENERATED = root
            try:
                artifacts.emit_fixed_development_if_audited()
                table = root / "fixed_development_table.tex"
                table.write_text("stale table")
                with self.assertRaises(SystemExit):
                    artifacts.emit_fixed_development_if_audited()
                table.unlink()
                audit = root / "tileplace_fixed_development_audit_2026-09-29.json"
                audit.write_text(json.dumps({"status": "partial"}))
                with self.assertRaises(SystemExit):
                    artifacts.emit_fixed_development_if_audited()
                matrix = root / "matrix.json"
                matrix.write_text("{}")
                audit.write_text(json.dumps({
                    "status": "pass", "implementation_sha256": "0f8a684ae7dc745fceb257d62a71bd8f34f61bf41db5cc515dfb641b6557d2a3",
                    "matrix": {"path": str(matrix), "sha256": "0" * 64},
                }))
                with self.assertRaises(SystemExit):
                    artifacts.emit_fixed_development_if_audited()
                self.assertFalse(table.exists())
            finally:
                artifacts.EXPERIMENTS, artifacts.GENERATED = previous


if __name__ == "__main__":
    unittest.main()
