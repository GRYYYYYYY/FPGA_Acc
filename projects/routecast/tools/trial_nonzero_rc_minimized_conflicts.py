"""Independently verify XML witnesses and every elimination/branch certificate."""
import json
from pathlib import Path
from fractions import Fraction
from collections import defaultdict
from pre_route_endpoints import sha
from nonzero_rc_search_context import load
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];out=root/'experiments/nonzero_rc_learning_selection_2026-10-06';parent=root/'experiments/nonzero_rc_multi_context_2026-10-06'
r=json.loads((out/'receipt.json').read_text());pool=json.loads((parent/'receipt.json').read_text());assert r['parent_receipt_sha256']==sha(parent/'receipt.json') and r['source_sha256']==sha(root/'tools/trial_nonzero_rc_learning_selection.py') and r['protocol_sha256']==sha(out/'protocol.json')
graph,digest,_,_,_,queries,_=load(root);assert digest==pool['graph_sha256'];audit=ImmutableXMLAudit(graph,digest);ids,classes,switches,_=read(graph);qmap={(q['net_id'],q['pin_index']):q for q in queries};keys=[];paths=[];foot=[];incoming=[];checked=0
for group in pool['candidates']:
 key=tuple(group['key']);assert key in qmap and key not in keys;keys.append(key);paths.append(group['paths']);fs=[];ps=[];q=qmap[key]
 for p in group['paths']:
  a=p['answer'];node=q['source'];seen={node};parents={};res,cap=classes[ids[node]];delay=res*cap/2
  for eid in a['physical_edge_ids']:
   e=audit.graph.edges[eid];assert e.source==node and e.sink not in seen;node=e.sink;seen.add(node);parents[node]=(e.source,eid);delay+=arc_delay(classes,switches,ids[node],e.switch_id)
  assert node==q['sink'] and delay==Fraction(a['delay'],pool['scale'])<=Fraction(1,10**9) and sorted(seen)==p['nodes'];assert [[n,*v] for n,v in parents.items()]==p['parents'];fs.append(seen);ps.append(parents);checked+=1
 foot.append(fs);incoming.append(ps)
assert set(keys)==set(qmap)
def compatible(i,a,j,b):
 if keys[i][0]!=keys[j][0]:return all(audit.caps[n]>=2 for n in foot[i][a]&foot[j][b])
 return all(audit.caps[n]>=1 for n in foot[i][a]|foot[j][b]) and all(incoming[i][a][n]==incoming[j][b][n] for n in incoming[i][a].keys()&incoming[j][b].keys())
# Independent compatibility reconstruction and full-domain propagation for each learned core.
from collections import deque
supports={};neighbors=[set() for _ in keys]
for i in range(len(keys)):
 for j in range(len(keys)):
  if i==j:continue
  rows=[{b for b in range(len(paths[j])) if compatible(i,a,j,b)} for a in range(len(paths[i]))]
  if any(len(row)!=len(paths[j]) for row in rows):supports[i,j]=rows;neighbors[j].add(i)
def verify_core(core):
 ds=[set(range(len(ps))) for ps in paths];seen=set()
 for i,a in core:
  assert i not in seen and a in ds[i];seen.add(i);ds[i]={a}
 queue=deque(supports)
 while queue:
  i,j=queue.popleft();old=ds[i];new={a for a in old if supports[i,j][a]&ds[j]}
  if new!=old:
   ds[i]=new
   if not new:return True
   queue.extend((k,i) for k in neighbors[i] if k!=j)
 return False

source_out=out;out=root/'experiments/nonzero_rc_minimized_conflicts_2026-10-06';out.mkdir()
verified=json.loads((source_out/'verification.json').read_text());assert verified['receipt_sha256']==sha(source_out/'receipt.json')
(out/'protocol.json').write_text(json.dumps({'first_cores':32,'policy':'Ascending literal single deletion pass, fresh full-domain AC after each removal; at most original core size attempts per core','parent_receipt_sha256':sha(source_out/'receipt.json'),'scope':'AC-irreducible conflict subsets only, not globally minimum cardinality or complete routing'},indent=2)+'\n')
records=[]
for index,original in enumerate(r['nogoods'][:32]):
 core=list(original);attempts=[];assert verify_core(core)
 for literal in original:
  trial=[v for v in core if v!=literal];contradiction=verify_core(trial);attempts.append({'removed':literal,'contradiction':contradiction})
  if contradiction:core=trial
 records.append({'parent_index':index,'original':original,'core':core,'attempts':attempts})
result={'records':records,'parent_receipt_sha256':sha(source_out/'receipt.json'),'pool_sha256':sha(parent/'receipt.json'),'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__)),'scope':'Subset cores separately validated before reuse; no search or native FULL/STA success claim'}
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print('cores',len(records),'literals',sum(len(v['original']) for v in records),'->',sum(len(v['core']) for v in records))
