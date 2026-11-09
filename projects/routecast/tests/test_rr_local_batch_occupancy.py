import unittest
import random
import test_rr_batch_occupancy as reference
from rr_local_batch_occupancy import LocalBatchOccupancy
from connection_golden import Result


class LocalTests(reference.BatchTests):
    def setUp(self):
        self.original = reference.BatchOccupancy
        reference.BatchOccupancy = LocalBatchOccupancy

    def tearDown(self):
        reference.BatchOccupancy = self.original

    def test_dirty_update_does_not_scan_or_copy_full_state(self):
        graph, old, new = self.prepare()
        ledger = LocalBatchOccupancy(graph)
        for cid in range(1000):
            self.assertEqual(ledger.update(cid, 1, cid // 2, 0, 5, old), Result.COMMITTED)
        class NoScan(dict):
            def items(self): raise AssertionError('whole-state scan')
            def keys(self): raise AssertionError('whole-state copy')
            def __iter__(self): raise AssertionError('whole-state iteration')
        original = ledger._states
        ledger._states = NoScan(original)
        ledger.rebuild = lambda: self.fail('full rebuild during commit')
        self.assertEqual(ledger.update_batch([self.row(0, 2, 6, new, 0),
                                             self.row(1, 2, 6, new, 0)]), Result.COMMITTED)
        self.assertEqual(ledger.occupancy[6], 1)
        self.assertEqual(ledger.occupancy[0], 499)

    def test_failure_precedence_and_random_differential_transactions(self):
        graph, old, new = self.prepare()
        oracle = self.original(graph)
        local = LocalBatchOccupancy(graph)
        for ledger in (oracle, local):
            self.assertEqual(ledger.update_batch([self.row(0, 1, 0, old)]), Result.COMMITTED)
        invalid_then_stale = [self.row(1, 1, 0, (-1,)), self.row(0, 1, 0, old)]
        self.assertEqual(local.update_batch(invalid_then_stale), Result.STALE)
        self.assertEqual(oracle.update_batch(invalid_then_stale), Result.STALE)
        rng = random.Random(101005)
        for _ in range(1000):
            rows = []
            for _ in range(rng.randrange(1, 5)):
                cid = rng.randrange(12)
                epoch = rng.randrange(1, 30)
                if rng.random() < .25:
                    row = dict(connection_id=cid, epoch=epoch, remove=True)
                else:
                    source = rng.choice((0, 6))
                    path = old if source == 0 else new
                    if rng.random() < .15:
                        path = (-1,)
                    row = self.row(cid, epoch, source, path, rng.randrange(4))
                rows.append(row)
            before = (local.states, local.occupancy)
            expected = oracle.update_batch(rows)
            self.assertEqual(local.update_batch(rows), expected)
            self.assertEqual(local.states, oracle.states)
            self.assertEqual(local.occupancy, oracle.occupancy)
            self.assertEqual(local.occupancy, local.rebuild())
            if expected != Result.COMMITTED:
                self.assertEqual((local.states, local.occupancy), before)


if __name__ == '__main__':
    unittest.main()
