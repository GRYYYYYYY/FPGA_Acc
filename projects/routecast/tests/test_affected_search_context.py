import unittest
from affected_search_context import FIELDS, plan


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.context = {key: 'a' * 64 for key in FIELDS}
        self.endpoint = {'graph_sha256': 'a' * 64, 'connections': [
            {'connection_id': 0, 'net_id': 0, 'source': 1, 'sink': 2},
            {'connection_id': 1, 'net_id': 0, 'source': 1, 'sink': 3},
            {'connection_id': 2, 'net_id': 1, 'source': 4, 'sink': 5}]}

    def test_same_endpoints_changed_context_cannot_retain_paths(self):
        for key in FIELDS:
            with self.subTest(key=key):
                changed = dict(self.context, **{key: 'b' * 64})
                endpoint = dict(self.endpoint)
                if key == 'graph_sha256':
                    endpoint['graph_sha256'] = 'b' * 64
                result = plan(self.endpoint, endpoint, self.context, changed)
                self.assertEqual(result['recompute_connection_ids'], [0, 1, 2])
                self.assertEqual(result['retained_connection_ids'], [])
                self.assertTrue(result['discard_previous_state'])

    def test_move_retains_only_outside_complete_net(self):
        moved = dict(self.endpoint, connections=[dict(r) for r in self.endpoint['connections']])
        moved['connections'][0]['sink'] = 6
        result = plan(self.endpoint, moved, self.context, self.context)
        self.assertEqual(result['mode'], 'incremental')
        self.assertEqual(result['recompute_connection_ids'], [0, 1])
        self.assertEqual(result['retained_connection_ids'], [2])

    def test_malformed_or_misbound_context_rejected(self):
        for context in ({}, dict(self.context, consumer_sha256='invalid'),
                        dict(self.context, graph_sha256='b' * 64)):
            with self.assertRaises(ValueError):
                plan(self.endpoint, self.endpoint, self.context, context)


if __name__ == '__main__':
    unittest.main()
