import unittest
from dynamic_net_dijkstra import search
from prepared_csr import U64


class MultiSinkTests(unittest.TestCase):
    def fields(self):
        return dict(node_ids=list(range(5)),row_offsets=[0,2,3,4,4,4],
                    edge_ids=[10,11,12,13],dest_ranks=[1,2,3,3],
                    costs=[1,2,1,1],capacities=[1]*5)

    def test_shared_source_sinks_unreachable_and_immutable(self):
        f=self.fields()
        results,potential,examined=search(f,0,[0,1,3,3,4],{0,1,3},{0:1,1:1,3:1})
        self.assertEqual(results[0],('FOUND',0,()))
        self.assertEqual(results[1],('FOUND',1,(10,)))
        self.assertEqual(results[3],('FOUND',2,(10,12)))
        self.assertEqual(results[4],('UNREACHABLE',None,None))
        with self.assertRaises(TypeError):potential[0]=9
        self.assertEqual(examined,4)

    def test_eligibility_and_invalid_cost(self):
        f=self.fields();f['costs'][0]=U64
        self.assertEqual(search(f,0,[3],set(),{})[0][3],('FOUND',3,(11,13)))
        f['capacities'][2]=0
        self.assertEqual(search(f,0,[3],set(),{})[0][3][0],'UNREACHABLE')
        f=self.fields();f['costs'][0]=0
        with self.assertRaises(ValueError):search(f,0,[3],set(),{})
        with self.assertRaises(ValueError):search(self.fields(),0,[3],{1},{})

if __name__=='__main__':unittest.main()
