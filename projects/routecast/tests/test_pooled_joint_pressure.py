import unittest
from types import SimpleNamespace
from unittest.mock import patch
from incremental_pooled_pressure import PooledPressure
from pooled_ledger_pressure_transaction import PooledLedgerPressureTransaction
from connection_golden import Result

class PooledJointTests(unittest.TestCase):
 def setUp(self):
  kinds=('SOURCE','CHANX','CHANX','SINK');graph=SimpleNamespace(nodes={i:SimpleNamespace(type=k,capacity=1) for i,k in enumerate(kinds)},edges=[SimpleNamespace(source=a,sink=b) for a,b in ((0,1),(1,3),(0,2),(2,3))]);f={k:[0]*4 for k in ('segments','xlow','xhigh','ylow','yhigh','layer')};f.update(types=[0,4,4,1],directions=[0,1,1,0],capacities=[1]*4);self.joint=PooledLedgerPressureTransaction(graph,f,'a'*64);self.assertEqual(self.joint.update_batch([self.row(0,1),self.row(1,1)]),Result.COMMITTED)
 def row(self,cid,epoch,path=(0,1)):return dict(connection_id=cid,epoch=epoch,net_id=cid,source=0,sink=3,edge_ids=path)
 def test_joint_pool_updates_and_stale_reject(self):
  self.assertEqual(set(self.joint.snapshot()['pressure_rows']),{1,2});self.assertEqual(self.joint.update_batch([self.row(0,2,(2,3))]),Result.COMMITTED);after=self.joint.snapshot();self.assertEqual(after['pressure_rows'],{});self.assertEqual(self.joint.update_batch([self.row(0,2)]),Result.STALE);self.assertEqual(self.joint.snapshot(),after)
 def test_refresh_and_serialization_failure_preserve_whole_pair(self):
  before=self.joint.snapshot()
  for method in ('refresh','payload'):
   with patch.object(PooledPressure,method,side_effect=ValueError('injected staging failure')):
    with self.assertRaises(ValueError):self.joint.update_batch([self.row(0,2,(2,3))])
   self.assertEqual(self.joint.snapshot(),before)
  self.assertEqual(self.joint.update_batch([self.row(0,2,(2,3))]),Result.COMMITTED)

if __name__=='__main__':unittest.main()
