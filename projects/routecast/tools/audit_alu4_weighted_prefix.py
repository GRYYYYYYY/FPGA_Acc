"""Audit a fixed completed checkpoint prefix without touching live producer."""
import json,time
from pathlib import Path
from rr_graph import read_rr_graph
from pin_choice_catalog import PinChoiceCatalog
from net_pressure_sketch import net_union
from pre_route_endpoints import sha
root=Path('experiments/alu4_full_weighted_pin_trial_2026-10-05');out=root/'prefix_audit.json'
assert not out.exists();start=time.monotonic();protocol=json.loads((root/'protocol.json').read_text());assert all(sha(p)==h for p,h in protocol['input_sha256'].items())
# The producer publishes numbered checkpoints in order; take only a bounded
# prefix with a later file already present, avoiding its currently open file.
files=sorted((root/'checkpoints').glob('*.json'),key=lambda p:int(p.stem))[:64];assert len(files)==64
assert len(list((root/'checkpoints').glob('*.json')))>64
snapshots={str(p):p.read_bytes() for p in files};digests={str(p):sha(p) for p in files};g=read_rr_graph('work/alu4_validation_capture_2026-10-05/rr_graph.xml');catalog=PinChoiceCatalog(g);bg=json.loads(Path('experiments/alu4_transfer_2026-10-05/prediction.json').read_text());rows={r['connection_id']:r for r in bg['connections']};users,demand=net_union(g,bg);eq=json.loads(Path('experiments/alu4_full_pin_equivalence_audit_2026-10-05/receipt.json').read_text());checks={r['cid']:r for r in eq['checks']};spans={}
for n,node in g.nodes.items():
 loc=dict(node.location);spans[n]=max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1 if node.type in {'CHANX','CHANY'} else 0
count=0
for file in files:
 cid=int(file.stem);r=rows[cid];q=json.loads(snapshots[str(file)]);assert set(map(int,q['paths']))==set(checks[cid]['physical_members']);old=catalog.witness(r['source'],r['sink'],r['physical_edge_ids'])
 for ptc,path in q['paths'].items():
  w=catalog.witness(r['source'],r['sink'],path);assert w['selected_ipin_ptc']==int(ptc) and w['selected_opin_ptc']==old['selected_opin_ptc'];cost=0
  for eid in path:
   n=g.edges[eid].sink;v=g.nodes[n];d=demand.get(n,0)-int(n in users[r['net_id']]);penalty=(256*max(0,d-v.capacity+1)+v.capacity-1)//v.capacity if n in spans and v.type in {'CHANX','CHANY'} and v.capacity>0 else 0;cost+=spans[n]+penalty
  assert cost==q['costs'][ptc];count+=1
assert count==2560 and all(sha(p)==h for p,h in digests.items())
record={'protocol_sha256':sha(root/'protocol.json'),'audit_source_sha256':sha(__file__),'checkpoint_sha256':digests,'requests_checked':64,'witnesses_checked':count,'physical_and_supplied_cost_exact':True,'wall_s':time.monotonic()-start,'scope':'First64 completed checkpoints only; not complete library, matching optimality or joint channel/tree/native legality'};out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k!='checkpoint_sha256'}),flush=True)
