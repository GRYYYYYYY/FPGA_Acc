import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'cpp_snapshot'))
from test_constrained_proposals import engine
from pack_snapshot import pack
from snapshot_codec import encode,decode

class PackTest(unittest.TestCase):
 def test_constrained_engine_records(self):
  for seed in range(12):
   reference=engine(seed);snapshot,types=pack(reference)
   result=decode(encode(snapshot))
   self.assertEqual(snapshot,result)
   positions={b[0]:p for b,p in zip(result['blocks'],result['positions'])}
   self.assertEqual(positions,reference.positions)
   for b in result['blocks']:
    self.assertEqual(types[b[1]],reference.block_by_id[b[0]]['logical_type'])
   reconstructed={}
   for axis,line,total,offset,count in result['prefix_lines']:
    entries=result['prefix_entries'][offset:offset+count]
    for i,(coordinate,_,before) in enumerate(entries):
     after=entries[i+1][2] if i+1<len(entries) else total
     edge=(coordinate,line,coordinate+1,line) if axis==0 else (line,coordinate,line,coordinate+1)
     reconstructed[edge]=after-before
   self.assertEqual(reconstructed,dict(reference.pressure_q16))
   self.assertEqual(result['routed_edges'],[(*edge,w) for edge,w in sorted(reference.path_edges_q16.items())])
   for index,u in enumerate(result['units']):
    members=tuple(row[0] for row in result['unit_members'][u[0]:u[0]+u[1]])
    self.assertEqual(members,reference.units[index])
    self.assertEqual(u[2],int(members in reference.fixed_units))
if __name__=='__main__':unittest.main()
