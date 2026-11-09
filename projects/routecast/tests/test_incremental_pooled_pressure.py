import unittest
from pooled_channel_pressure import rows, payload
from incremental_pooled_pressure import PooledPressure


class IncrementalPoolTests(unittest.TestCase):
    def setUp(self):
        self.fields = {key: [0, 0, 0] for key in
                       ('segments', 'xlow', 'xhigh', 'ylow', 'yhigh', 'layer')}
        self.fields.update(types=[4, 4, 5], directions=[1, 1, 2], capacities=[1, 3, 1])
        self.cache = PooledPressure(self.fields)

    def test_one_dirty_track_refreshes_all_pool_members_and_can_remove_pool(self):
        self.cache.refresh({0: 3}, [0])
        self.assertIn(1, self.cache.rows)
        self.assertEqual(self.cache.payload('a' * 64), payload(3, 'a' * 64, rows(self.fields, {0: 3})[0]))
        report = self.cache.refresh({}, [0])
        self.assertEqual(report['refreshed_group_members'], 2)
        self.assertEqual(self.cache.rows, {})

    def test_invalid_late_dirty_item_leaves_all_state_unchanged(self):
        self.cache.refresh({0: 3}, [0])
        before = (dict(self.cache.rows), dict(self.cache.node_excess), dict(self.cache.group_excess))
        with self.assertRaises(ValueError):
            self.cache.refresh({0: 1}, [0, -1])
        self.assertEqual((self.cache.rows, self.cache.node_excess, self.cache.group_excess), before)


if __name__ == '__main__':
    unittest.main()
