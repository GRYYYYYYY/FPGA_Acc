"""Reload every resident subset native result with original VPR; preserve failures."""
import sys,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from canonical_reload_identity_only_v2 import canonical_reload,binary,identity
from pre_route_endpoints import sha
from source_binding_v2 import closure
from rr_graph import read_rr_graph
src=R/'experiments/resident_subset_native_v1_2026-10-07'
out=R/'experiments/resident_subset_canonical_v1_2026-10-07'
out.mkdir()
receipt=src/'receipt.json'
data=json.loads(receipt.read_text())
assert all(sha(k)==v for k,v in data['bindings'].items())
bindings={**closure([Path(__file__)]),str(receipt):sha(receipt),str(binary):sha(binary),str(identity):sha(identity)}
class Inventory:
 def __init__(self,path):
  self.path=path;g=read_rr_graph(path);self.digest=g.sha256
  self.nodes={n:(x.type,dict(x.location)) for n,x in g.nodes.items()}
 def validate(self,path,digest):
  assert path==self.path and digest==self.digest and sha(path)==digest
rows=[]
for original in data['rows']:
 name=original['name'];start=time.perf_counter();row={'name':name,'status':'FAILED'}
 try:
  assert original['native_status']=='SEEDED_FULL_STA_ENDPOINT_CAPACITY_PASS'
  graph=Path(original['command'][original['command'].index('--read_rr_graph')+1])
  p={**original,'width':128,'decision':'R'}
  result=canonical_reload(p,src/name,out/name,Inventory(graph))
  row.update(status='ORIGINAL_VPR_CANONICAL_FULL_STA_PASS',result=result)
 except Exception as error:row['error']=repr(error)
 row['actual_canonical_stage_seconds']=time.perf_counter()-start
 rows.append(row)
 (out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(name,row['status'],row.get('error'),flush=True)
assert all(sha(k)==v for k,v in bindings.items())
(out/'receipt.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'scope':'Canonical packed NET/pin remapping and original VPR FULL/STA reload only; no cold comparison or complete workflow gain.'},indent=2)+'\n')
assert all(r['status']=='ORIGINAL_VPR_CANONICAL_FULL_STA_PASS' for r in rows)
