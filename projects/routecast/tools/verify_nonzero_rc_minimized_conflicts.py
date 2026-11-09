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

source_out=out;out=root/'experiments/nonzero_rc_minimized_conflicts_2026-10-06';result=json.loads((out/'receipt.json').read_text());assert result['parent_receipt_sha256']==sha(source_out/'receipt.json') and result['pool_sha256']==sha(parent/'receipt.json') and result['protocol_sha256']==sha(out/'protocol.json') and result['source_sha256']==sha(root/'tools/trial_nonzero_rc_minimized_conflicts.py')
supports={(i,a,j):{b for b in range(len(paths[j])) if compatible(i,a,j,b)} for i in range(len(keys)) for a in range(len(paths[i])) for j in range(len(keys)) if i!=j}
def contradiction(core):
 domains=[set(range(len(ps))) for ps in paths]
 for i,a in core:assert a in domains[i];domains[i]={a}
 changed=True
 while changed:
  changed=False
  for i in range(len(keys)):
   for a in sorted(domains[i]):
    if any(not supports[i,a,j]&domains[j] for j in range(len(keys)) if i!=j):domains[i].remove(a);changed=True
   if not domains[i]:return True
 return False
assert len(result['records'])==32
attempts=0
for index,record in enumerate(result['records']):
 assert record['parent_index']==index and record['original']==r['nogoods'][index];core=list(record['original']);assert contradiction(core)
 assert [a['removed'] for a in record['attempts']]==record['original']
 for attempt in record['attempts']:
  trial=[v for v in core if v!=attempt['removed']];answer=contradiction(trial);assert answer==attempt['contradiction'];attempts+=1
  if answer:core=trial
 assert core==record['core'] and contradiction(core)
 assert all(not contradiction([v for v in core if v!=literal]) for literal in core)
(out/'verification.json').write_text(json.dumps({'cores_checked':32,'deletion_attempts_checked':attempts,'original_literals':sum(len(c['original']) for c in result['records']),'minimized_literals':sum(len(c['core']) for c in result['records']),'AC_irreducible':True,'minimum_cardinality_claimed':False,'receipt_sha256':sha(out/'receipt.json'),'scope':'Independent XML compatibility and full-sweep propagation verify every deletion and final core irreducibility; no complete selection/native legality/performance claim.'},indent=2)+'\n');print('verified32 AC-irreducible cores,',attempts,'deletions')
