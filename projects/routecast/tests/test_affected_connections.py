import unittest
from affected_connections import affected

def ep(rows):return {'graph_sha256':'same','connections':[dict(connection_id=c,net_id=n,source=s,sink=t) for c,n,s,t in rows]}

class AffectedTests(unittest.TestCase):
    def test_source_group_dependency_and_whole_net(self):
        old=ep([(0,7,0,5),(1,7,0,6),(2,8,0,9),(3,9,20,21)])
        new=ep([(0,7,10,5),(1,7,10,6),(2,8,0,9),(3,9,20,21)])
        r=affected(old,new)
        self.assertEqual(r['recompute_connection_ids'],[0,1,2]);self.assertEqual(r['retained_connection_ids'],[3])
        self.assertEqual(r['affected_source_ids'],[0,10])
    def test_delete_add_and_noop(self):
        old=ep([(0,7,0,5),(1,8,10,6)]);new=ep([(1,8,10,6),(2,7,0,9)])
        r=affected(old,new);self.assertEqual(r['remove_connection_ids'],[0]);self.assertEqual(r['recompute_connection_ids'],[2])
        self.assertEqual(affected(old,old)['recompute_connection_ids'],[])
    def test_invalid_identity_or_graph_requires_rejection(self):
        old=ep([(0,7,0,5)])
        with self.assertRaises(ValueError):affected(old,{**old,'graph_sha256':'changed'})
        with self.assertRaises(ValueError):affected(old,ep([(0,7,0,5),(0,7,0,6)]))
        with self.assertRaises(ValueError):affected(old,ep([(0,7,0,5),(1,7,10,6)]))

if __name__=='__main__':unittest.main()
