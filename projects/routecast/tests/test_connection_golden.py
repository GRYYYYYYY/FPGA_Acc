import random
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from connection_golden import Edge, Golden, Result, UINT32_MAX


def exhaustive_path(nodes, edges, source, sink, limit):
    # Independent simple-path enumeration, including parallel edges.
    answers = []
    def visit(node, visited, path, cost):
        if node == sink:
            answers.append((cost, len(path), tuple(path)))
            return
        if len(path) == limit:
            return
        for eid, edge in enumerate(edges):
            if edge.source == node and edge.capacity and edge.sink not in visited:
                visit(edge.sink, visited | {edge.sink}, path + [eid], cost + edge.cost)
    visit(source, {source}, [], 0)
    return min(answers)[2] if answers else None


class GoldenTests(unittest.TestCase):
    def model(self):
        return Golden(4, [Edge(0,1), Edge(1,2), Edge(0,2,3), Edge(2,3)], 4)

    def test_replace_remove_tombstone(self):
        g = self.model()
        self.assertEqual(g.update(7,1,0,2,256),Result.COMMITTED)
        self.assertEqual(g.demand,(256,256,0,0))
        self.assertEqual(g.update(7,2,2,3,512),Result.COMMITTED)
        self.assertEqual(g.demand,(0,0,0,512))
        self.assertEqual(g.update(7,3,remove=True),Result.COMMITTED)
        self.assertEqual(g.demand,(0,0,0,0))
        self.assertEqual(g.update(7,2,0,2,256),Result.STALE)
        self.assertEqual(g.update(7,4,0,0,256),Result.COMMITTED)
        self.assertEqual(g.states[7].connection.path,())

    def test_failures_preserve_path_epoch_and_demand(self):
        g = self.model(); g.update(1,1,0,2,256)
        before = (g.states,g.demand)
        for args,result in [((1,2,3,0,256),Result.NO_PATH),
                            ((1,2,0,99,256),Result.INVALID),
                            ((1,1,0,2,512),Result.STALE)]:
            self.assertEqual(g.update(*args),result)
            self.assertEqual((g.states,g.demand),before)
        self.assertEqual(g.update(1,2,0,2,512),Result.COMMITTED)

    def test_overflow_rollback_and_overlap(self):
        g = self.model(); g.update(1,1,0,2,UINT32_MAX)
        before = (g.states,g.demand)
        self.assertEqual(g.update(2,1,0,2,1),Result.OVERFLOW)
        self.assertEqual((g.states,g.demand),before)
        self.assertEqual(g.update(1,2,0,2,UINT32_MAX),Result.COMMITTED)
        self.assertEqual(g.demand,g.rebuild())

    def test_unknown_remove_retains_epoch(self):
        g = self.model()
        self.assertEqual(g.update(4,9,remove=True),Result.COMMITTED)
        self.assertEqual(g.update(4,8,0,2,256),Result.STALE)
        self.assertEqual(g.update(4,10,0,2,256),Result.COMMITTED)

    def test_input_validation(self):
        for edges in [[Edge(0,4)], [Edge(0,1,-1)], [Edge(0,1,capacity=-1)]]:
            with self.assertRaises(ValueError): Golden(4,edges)
        g = self.model()
        for args in [(True,1,0,2,1), (1,0,0,2,1), (1,1,0,2,-1), (1,1,0,2,UINT32_MAX+1)]:
            self.assertEqual(g.update(*args),Result.INVALID)
        self.assertEqual(g.update(1,1,0,2,1,remove=True),Result.INVALID)
        self.assertEqual(g.states,{})

    def test_hop_constraint_and_zero_capacity(self):
        g = Golden(3,[Edge(0,1,0),Edge(1,2,0),Edge(0,2,5),Edge(0,2,0,0)],1)
        self.assertEqual(g.path(0,2),(2,))
        self.assertIsNone(Golden(3,[Edge(0,1),Edge(1,2)],1).path(0,2))
        self.assertEqual(Golden(1,[],0).path(0,0),())

    def test_exhaustive_search_differential(self):
        rng = random.Random(20261004)
        for case in range(100):
            nodes = rng.randrange(2,7)
            edges = [Edge(rng.randrange(nodes),rng.randrange(nodes),rng.randrange(5),rng.randrange(3))
                     for _ in range(rng.randrange(1,15))]
            hops = rng.randrange(0,7)
            g = Golden(nodes,edges,hops)
            for source in range(nodes):
                for sink in range(nodes):
                    with self.subTest(case=case,source=source,sink=sink):
                        self.assertEqual(g.path(source,sink),exhaustive_path(nodes,edges,source,sink,hops))

    def test_randomized_incremental_vs_full_rebuild(self):
        rng = random.Random(4926)
        edges = [Edge(i,j,1+abs(i-j)) for i in range(6) for j in range(6) if i != j]
        g = Golden(6,edges,6)
        expected = {}
        for step in range(1000):
            cid = rng.randrange(20)
            old_epoch = expected.get(cid,(0,None))[0]
            epoch = old_epoch + 1 if rng.random() > .2 else old_epoch
            remove = rng.random() < .25
            source,sink,demand = rng.randrange(6),rng.randrange(6),rng.randrange(1025)
            before = (g.states,g.demand)
            result = g.update(cid,epoch,remove=True) if remove else g.update(cid,epoch,source,sink,demand)
            if result == Result.COMMITTED:
                expected[cid] = (epoch,None if remove else (source,sink,demand))
            else:
                self.assertEqual((g.states,g.demand),before)
            full = [0]*len(edges)
            for _, connection in expected.values():
                if connection is not None:
                    s,t,q = connection
                    for eid in exhaustive_path(6,edges,s,t,6): full[eid] += q
            self.assertEqual(g.demand,tuple(full),f'step={step}')
            self.assertEqual(g.demand,g.rebuild())


if __name__ == '__main__': unittest.main()
