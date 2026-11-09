"""Full snapshot tree-delay float32 recurrence under independently checked zero-RC graph."""
import json,struct,math
from pathlib import Path
from pre_route_endpoints import sha
from buffered_rc_node_classes import read
R=Path(__file__).resolve().parents[1];O=R/'experiments/mmc_native_iteration_state_observer_v1_2026-10-10'
v=json.loads((O/'verification.json').read_text());assert v['route_bytes_equal_fully_audited_cold'];assert all(sha(p)==h for p,h in v['bindings'].items())
ep=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json';e=json.loads(ep.read_text());graph=Path(e['inputs']['graph']['path'])
indices,classes,switches,digest=read(graph);assert digest==e['graph_sha256'] and len(indices)==904438 and all(r==0 and c==0 for r,c in classes)
def f32(x):return struct.unpack('f',struct.pack('f',x))[0]
sw={k:f32(float(delay)) for k,(resistance,delay) in switches.items()};rows=[]
for iteration in range(1,22):
 p=O/'states'/f'round_{iteration}.tsv';assert sha(p)==v['bindings'][str(p)];trees={};count=0
 with p.open() as s:
  for line in s:
   fields=line.split()
   if fields[0]!='T':continue
   net,n,parent,switch=map(int,fields[1:5]);delay=f32(float(fields[5]));assert math.isfinite(delay) and delay>=0;count+=1
   tree=trees.setdefault(net,{})
   if n in tree:assert tree[n]==(parent,switch,delay)
   tree[n]=(parent,switch,delay)
 for net,tree in trees.items():
  for n,(parent,switch,delay) in tree.items():
   expected=0.0 if parent==-1 else f32(tree[parent][2]+sw[switch]);assert delay==expected,(iteration,net,n,parent,delay,expected)
 rows.append({'iteration':iteration,'tree_records':count});print('TREE DELAY',iteration,count,flush=True)
assert all(sha(p)==h for p,h in v['bindings'].items())
f=O/'tree_delay_audit_v1.json';assert not f.exists();f.write_text(json.dumps({'bindings':{**v['bindings'],str(O/'verification.json'):sha(O/'verification.json'),str(graph):digest,str(ep):sha(ep),str(Path(__file__).resolve()):sha(Path(__file__)),str(R/'tools/buffered_rc_node_classes.py'):sha(R/'tools/buffered_rc_node_classes.py')},'all21rounds_tree_delay_float32_recurrence_pass':True,'all_original_graph_node_R_C_zero':True,'rows':rows,'scope':'Full snapshot root-zero/parent-delay-plus-original-switch-Tdel float32 recurrence under all-node zero RC graph. Does not certify manifest pin budgets, full timing analysis, edge membership (separate audit), native equivalence or quality.'},indent=2)+'\n')
