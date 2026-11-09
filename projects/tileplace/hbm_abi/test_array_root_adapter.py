import subprocess,unittest,tempfile
from pathlib import Path
from pack_snapshot import pack
from native_snapshot_adapter import NativeSnapshotEngine
from test_constrained_proposals import engine
ROOT=Path(__file__).resolve().parent
class ArrayRootAdapterTest(unittest.TestCase):
 def test_resident_adapter(self):
  with tempfile.TemporaryDirectory() as d:
   binary=Path(d)/'server';subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(ROOT/'array_root_native_server.cpp'),'-o',str(binary)],check=True)
   NativeSnapshotEngine.binary=binary;NativeSnapshotEngine.instances=[];NativeSnapshotEngine.checks=[]
   for seed in range(12):
    e=engine(seed);e.__class__=NativeSnapshotEngine;e._start_snapshot_server()
    try:
     saved=e.snapshot();pressure=dict(e.pressure_q16);timing=(dict(e.path_edges_q16),set(e.focus_blocks))
     selected=[]
     for color in range(4):
      batch,_=e.propose_color(color);selected.extend(batch)
     self.assertTrue(selected);e.apply([selected[0]])
     e.pressure_q16={edge:weight*3 for edge,weight in pressure.items()}
     e.update_timing_feedback(({edge:weight*2 for edge,weight in timing[0].items()},{6}))
     for color in range(4):e.propose_color(color)
     e.restore(saved);e.pressure_q16=pressure;e.update_timing_feedback(timing)
     for color in range(4):e.propose_color(color)
    finally:e.close()
if __name__=='__main__':unittest.main()
