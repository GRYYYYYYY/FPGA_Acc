import sys,subprocess,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT.parent/'array_transactions'),str(ROOT.parent/'hbm_abi'),str(ROOT.parent/'cpp_snapshot')]
from fast_transaction_adapter import FastTransactionEngine
from compare_proposals import TilePlaceV2Engine
from test_constrained_proposals import engine
def dense_engine(seed):
 e=engine(seed)
 import random
 points=[(x,y,0,seed%2) for x in range(3) for y in range(3)]
 random.Random(90000+seed).shuffle(points)
 e.positions=dict(zip(range(7),points[:7]));e.units=[(block,) for block in range(7)]
 e.unit_by_block={block:(block,) for block in range(7)};e.fixed_units=set()
 e.site_by_loc={point:{'physical_type':'clb'} for point in points};e.sites_by_page_type.clear()
 for point,site in e.site_by_loc.items():e.sites_by_page_type[(e.page_key(point),site['physical_type'])].append(point)
 for block,point in e.positions.items():e.block_by_id[block]={'logical_type':'clb','initial':dict(zip(['x','y','subtile','layer'],point))}
 e._net_cost_cache={}
 return e

class DenseCapacityAdapterTest(unittest.TestCase):
 def test_limits_larger_than_sites_commit_feedback_restore(self):
  with tempfile.TemporaryDirectory() as d:
   binary=Path(d)/'server'
   subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(ROOT/'transaction_native_server.cpp'),'-o',str(binary)],check=True)
   FastTransactionEngine.binary=binary;FastTransactionEngine.instances=[];FastTransactionEngine.checks=[]
   for seed in range(8):
    reference=dense_engine(seed);e=dense_engine(seed);e.__class__=FastTransactionEngine;e._start_snapshot_server()
    try:
     saved=e.snapshot();initial=reference.snapshot();pressure=dict(reference.pressure_q16);timing=(dict(reference.path_edges_q16),set(reference.focus_blocks))
     def compare():
      selected=[]
      for color in range(4):
       expected,stats=reference.propose_color(color)
       with patch.object(TilePlaceV2Engine,'propose_color',side_effect=AssertionError('full Python enumeration invoked')):
        actual,actual_stats=e.propose_color(color)
       self.assertEqual(actual_stats,stats)
       self.assertEqual([(t.transaction_id,t.score_q20) for t in actual],[(t.transaction_id,t.score_q20) for t in expected])
       selected.extend(actual)
      return selected
     selected=compare();self.assertTrue(selected);e.apply([selected[0]]);reference.apply([selected[0]])
     updated={edge:weight*3 for edge,weight in pressure.items()};e.pressure_q16=updated;reference.pressure_q16=updated
     refreshed=({edge:weight*2 for edge,weight in timing[0].items()},{6});e.update_timing_feedback(refreshed);reference.update_timing_feedback(refreshed)
     compare();e.restore(saved);reference.restore(initial);e.pressure_q16=pressure;reference.pressure_q16=pressure;e.update_timing_feedback(timing);reference.update_timing_feedback(timing);compare()
    finally:e.close()
   self.assertEqual(len(FastTransactionEngine.checks),96)
if __name__=='__main__':unittest.main()
