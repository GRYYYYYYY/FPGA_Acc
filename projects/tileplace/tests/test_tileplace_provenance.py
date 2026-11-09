"""Regression coverage for drift that counts and final QoR cannot detect."""

import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))
from tileplace_provenance import feedback_identity, source_snapshot, file_snapshot, verify_files, verify_implementation
from tileplace_vpr import ContractError


class ProvenanceTests(unittest.TestCase):
    def test_same_count_different_edges_have_different_identity(self):
        payload = {"edges": [{"source": 1, "sink": 2, "weight": 8}],
                   "inputs": {"report": {"path": "/old"}}}
        moved = copy.deepcopy(payload)
        moved["inputs"]["report"]["path"] = "/new"
        self.assertEqual(feedback_identity(payload), feedback_identity(moved))
        moved["edges"][0]["sink"] = 3
        self.assertNotEqual(feedback_identity(payload), feedback_identity(moved))

    def test_source_or_parser_changes_reject_seal_and_file_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "source.py"
            path.write_text("VERSION = 1\n")
            parser = {"mode": "fixed", "pattern": "a"}
            frozen = source_snapshot([path], parser)
            verify_implementation(source_snapshot([path], parser), frozen)
            with self.assertRaises(ContractError):
                verify_implementation(source_snapshot([path], {"mode": "fixed", "pattern": "b"}), frozen)
            records = file_snapshot([path])
            path.write_text("VERSION = 2\n")
            with self.assertRaises(ContractError):
                verify_files(records)
            with self.assertRaises(ContractError):
                verify_implementation(source_snapshot([path], parser), frozen)


if __name__ == "__main__":
    unittest.main()
