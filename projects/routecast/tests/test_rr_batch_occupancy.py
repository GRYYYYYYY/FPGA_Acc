from dataclasses import replace
import random,unittest
import test_hybrid_repair as fixture
from hybrid_repair import repair
from rr_graph import RREdge
from rr_batch_occupancy import BatchOccupancy
from connection_golden import Result

class BatchTests(unittest.TestCase):
    def prepare(self):
        g,e,c=fixture.RepairTests().setup_case();path=repair(g,e,c)['connections'][0]['physical_edge_ids']
        nodes=dict(g.nodes);nodes[6]=replace(nodes[0],id=6)
        first=g.edges[path[0]];newpath=(len(g.edges),)+tuple(path[1:])
        g=replace(g,nodes=nodes,edges=g.edges+(RREdge(6,first.sink,first.switch_id,()),))
        return g,tuple(path),newpath
    def row(self,cid,epoch,source,path,net=7):
        return dict(connection_id=cid,epoch=epoch,net_id=net,source=source,sink=5,edge_ids=path)
    def test_source_move_requires_all_active_connections_and_is_atomic(self):
        g,old,new=self.prepare();ledger=BatchOccupancy(g)
        self.assertEqual(ledger.update_batch([self.row(0,1,0,old),self.row(1,1,0,old)]),Result.COMMITTED)
        before=(ledger.states,ledger.occupancy)
        self.assertEqual(ledger.update_batch([self.row(0,2,6,new)]),Result.INVALID)
        self.assertEqual((ledger.states,ledger.occupancy),before)
        self.assertEqual(ledger.update_batch([self.row(1,2,6,new),self.row(0,2,6,new)]),Result.COMMITTED)
        self.assertEqual(ledger.occupancy[0],0);self.assertEqual(ledger.occupancy[6],1)
        self.assertEqual(ledger.occupancy,ledger.rebuild())
    def test_invalid_second_path_stale_duplicate_and_tombstone(self):
        g,old,new=self.prepare();ledger=BatchOccupancy(g)
        ledger.update_batch([self.row(0,1,0,old)]);before=(ledger.states,ledger.occupancy)
        for rows in ([self.row(0,2,0,old),self.row(1,1,6,(-1,))],
                     [self.row(0,1,0,old)], [self.row(0,2,0,old),self.row(0,3,0,old)]):
            self.assertNotEqual(ledger.update_batch(rows),Result.COMMITTED)
            self.assertEqual((ledger.states,ledger.occupancy),before)
        self.assertEqual(ledger.update_batch([{'connection_id':9,'epoch':4,'remove':True}]),Result.COMMITTED)
        self.assertEqual(ledger.update_batch([self.row(9,3,0,old)]),Result.STALE)
    def test_proposal_fork_isolates_epochs_refs_and_root_move(self):
        g,old,new=self.prepare();parent=BatchOccupancy(g)
        parent.update_batch([self.row(0,1,0,old),self.row(1,1,0,old)])
        snapshot=(parent.states,parent.occupancy);branch=parent.fork()
        self.assertIs(branch.graph,parent.graph)
        self.assertEqual(branch.update_batch([self.row(0,2,6,new),self.row(1,2,6,new)]),Result.COMMITTED)
        self.assertEqual((parent.states,parent.occupancy),snapshot)
        self.assertEqual(parent.update_batch([{'connection_id':9,'epoch':3,'remove':True}]),Result.COMMITTED)
        self.assertNotIn(9,branch.states)
        self.assertEqual(branch.occupancy,branch.rebuild())

    def test_random_net_moves_against_independent_union(self):
        g,old,new=self.prepare();ledger=BatchOccupancy(g);rng=random.Random(101004);model={};epochs={}
        for step in range(500):
            net=rng.randrange(5);root=rng.choice((0,6));path=old if root==0 else new
            rows=[]
            for cid in (net*2,net*2+1):
                epochs[cid]=epochs.get(cid,0)+1
                if rng.random()<.25:
                    rows.append(dict(connection_id=cid,epoch=epochs[cid],remove=True));model.pop(cid,None)
                else:
                    rows.append(self.row(cid,epochs[cid],root,path,net));model[cid]=(net,root,path)
            self.assertEqual(ledger.update_batch(rows),Result.COMMITTED)
            users={n:set() for n in g.nodes}
            for net,root,path in model.values():
                users[root].add(net)
                for eid in path:users[g.edges[eid].sink].add(net)
            self.assertEqual(ledger.occupancy,{n:len(v) for n,v in users.items()})

if __name__=='__main__':unittest.main()
