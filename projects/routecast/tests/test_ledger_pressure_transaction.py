import unittest
from types import SimpleNamespace
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event, current_thread
from rr_local_batch_occupancy import LocalBatchOccupancy
from connection_golden import Result
from incremental_channel_pressure import ChannelPressure
from ledger_pressure_transaction import LedgerPressureTransaction


class JointTests(unittest.TestCase):
    def setUp(self):
        kinds = ('SOURCE', 'CHANX', 'CHANY', 'SINK')
        graph = SimpleNamespace(nodes={i: SimpleNamespace(type=k, capacity=1) for i, k in enumerate(kinds)},
                                edges=[SimpleNamespace(source=a, sink=b) for a, b in ((0, 1), (1, 3), (0, 2), (2, 3))])
        self.joint = LedgerPressureTransaction(graph, [0, 4, 5, 1], [1] * 4, 'a' * 64)
        self.assertEqual(self.joint.update_batch([self.row(0, 1), self.row(1, 1)]), Result.COMMITTED)

    def row(self, cid, epoch, path=(0, 1)):
        return dict(connection_id=cid, epoch=epoch, net_id=cid, source=0, sink=3, edge_ids=path)

    def test_replacement_updates_payload_and_preserves_snapshot(self):
        old = self.joint.snapshot()
        self.assertIn('1 1 2\n', old['payload'])
        self.assertEqual(self.joint.update_batch([self.row(0, 2, (2, 3))]), Result.COMMITTED)
        new = self.joint.snapshot()
        self.assertEqual(new['occupancy'][1], 1)
        self.assertEqual(new['pressure_rows'], {})
        self.assertIn('1 1 2\n', old['payload'])

    def test_pressure_failure_leaves_epoch_paths_occupancy_and_payload(self):
        old = self.joint.snapshot()
        with patch.object(ChannelPressure, 'refresh', side_effect=ValueError('injected pressure failure')):
            with self.assertRaises(ValueError):
                self.joint.update_batch([self.row(0, 2, (2, 3))])
        self.assertEqual(self.joint.snapshot(), old)
        self.assertEqual(self.joint.update_batch([self.row(0, 2, (2, 3))]), Result.COMMITTED)

    def test_stale_and_mixed_invalid_batch_leave_pair_unchanged(self):
        old = self.joint.snapshot()
        self.assertEqual(self.joint.update_batch([self.row(0, 1)]), Result.STALE)
        self.assertEqual(self.joint.update_batch([self.row(0, 2, (2, 3)), self.row(1, 2, (-1,))]), Result.INVALID)
        self.assertEqual(self.joint.snapshot(), old)

    def test_caller_mutation_after_validation_cannot_change_dirty_set(self):
        row = self.row(0, 2, [2, 3])
        updates = [row]
        original = LocalBatchOccupancy.update_batch

        def mutate_after_validation(ledger, requests):
            result = original(ledger, requests)
            row['connection_id'] = 999
            row['edge_ids'][:] = [-1]
            updates.clear()
            return result

        with patch.object(LocalBatchOccupancy, 'update_batch', mutate_after_validation):
            self.assertEqual(self.joint.update_batch(updates), Result.COMMITTED)
        snapshot = self.joint.snapshot()
        self.assertEqual(snapshot['states'][0][0], 2)
        self.assertEqual(snapshot['occupancy'][1], 1)
        self.assertEqual(snapshot['pressure_rows'], {})

    def test_same_epoch_competing_writers_commit_once(self):
        barrier = Barrier(2)

        def commit():
            barrier.wait(timeout=5)
            return self.joint.update_batch([self.row(0, 2, (2, 3))])

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(commit) for _ in range(2)]
            statuses = [f.result(timeout=5) for f in futures]
        self.assertCountEqual(statuses, [Result.COMMITTED, Result.STALE])
        self.assertEqual(self.joint.snapshot()['pressure_rows'], {})

    def test_reader_cannot_observe_staged_ledger_before_pressure_publication(self):
        staged, release, reader_attempted = Event(), Event(), Event()
        original_refresh = ChannelPressure.refresh
        original_lock = self.joint._lock

        class ObservedLock:
            def __enter__(self):
                if current_thread().name.startswith('snapshot-reader'):
                    reader_attempted.set()
                original_lock.acquire()

            def __exit__(self, *args):
                original_lock.release()

        self.joint._lock = ObservedLock()

        def pause_pressure(cache, occupancy, dirty):
            original_refresh(cache, occupancy, dirty)
            staged.set()
            if not release.wait(timeout=5):
                raise RuntimeError('test publication barrier timed out')

        with patch.object(ChannelPressure, 'refresh', pause_pressure):
            with ThreadPoolExecutor(max_workers=1) as writers, ThreadPoolExecutor(
                    max_workers=1, thread_name_prefix='snapshot-reader') as readers:
                writer = writers.submit(self.joint.update_batch, [self.row(0, 2, (2, 3))])
                try:
                    self.assertTrue(staged.wait(timeout=5))
                    reader = readers.submit(self.joint.snapshot)
                    self.assertTrue(reader_attempted.wait(timeout=5))
                    self.assertFalse(reader.done())
                finally:
                    release.set()
                self.assertEqual(writer.result(timeout=5), Result.COMMITTED)
                snapshot = reader.result(timeout=5)
        self.assertEqual(snapshot['states'][0][0], 2)
        self.assertEqual(snapshot['occupancy'][1], 1)
        self.assertEqual(snapshot['pressure_rows'], {})


if __name__ == '__main__':
    unittest.main()
