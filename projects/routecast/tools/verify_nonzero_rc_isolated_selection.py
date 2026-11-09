"""Independently verify XML witnesses and every elimination/branch certificate."""
import json
from pathlib import Path
from fractions import Fraction
from collections import defaultdict
from pre_route_endpoints import sha
from nonzero_rc_search_context import load
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];out=root/'experiments/nonzero_rc_isolated_selection_2026-10-06';parent=root/'experiments/nonzero_rc_pair_avoidance_2026-10-06'
r=json.loads((out/'receipt.json').read_text());pool=json.loads((parent/'receipt.json').read_text());assert r['parent_sha256']==sha(parent/'receipt.json') and r['python_sha256']==sha(root/'tools/trial_nonzero_rc_isolated_selection.py') and r['protocol_sha256']==sha(out/'protocol.json')
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

assert r['constraints_sha256']==sha(out/'constraints.txt') and r['cpp_sha256']==sha(root/'tools/native_candidate_selection/isolated_search.cpp') and r['binary_sha256']==sha(out/'search')
tokens=iter(map(int,(out/'constraints.txt').read_text().split()));assert next(tokens)==len(keys) and next(tokens)==200000
assert [next(tokens) for _ in keys]==list(map(len,paths));matrix_rows=0
for i in range(len(keys)):
 for j in range(len(keys)):
  if i==j:continue
  for a in range(len(paths[i])):
   expected=sum(1<<b for b in range(len(paths[j])) if compatible(i,a,j,b));assert next(tokens)==expected;matrix_rows+=1
assert next(tokens,None) is None
possible_owners=defaultdict(set)
for i,ps in enumerate(foot):
 for ns in ps:
  for n in ns:possible_owners[n].add(keys[i][0])
assert all(audit.caps[n]==1 or audit.caps[n]>=len(nets) for n,nets in possible_owners.items())
complete=False
if r['status']=='FOUND':
 assert len(r['selected'])==len(keys);owners=defaultdict(set);parents=defaultdict(set)
 for i,a in enumerate(r['selected']):
  assert 0<=a<len(paths[i])
  for n in foot[i][a]:owners[n].add(keys[i][0])
  for n,parent_edge in incoming[i][a].items():parents[keys[i][0],n].add(parent_edge)
 assert all(len(nets)<=audit.caps[n] for n,nets in owners.items()) and all(len(v)==1 for v in parents.values());complete=True
else:assert r['status'] in ('SELECTION_LIMIT','EXHAUSTED_UNCERTIFIED') and r['selected'] is None
assert 0<r['states']<=200000
assert r['isolation_log_sha256']==sha(out/'isolation.tsv');logged=0
for line in (out/'isolation.tsv').read_text().splitlines():
 i,a,*masks=map(int,line.split());assert len(masks)==len(keys);domains=[{b for b in range(len(paths[j])) if mask>>b&1} for j,mask in enumerate(masks)];assert all(domains) and len(domains[i])>1 and a==min(domains[i])
 assert all(compatible(i,b,j,c) for j in range(len(keys)) if j!=i for b in domains[i] for c in domains[j]);logged+=1
assert logged==min(r['isolation_fixes'],256)
(out/'verification.json').write_text(json.dumps({'logged_isolation_events_checked':logged,'all_isolation_events_logged':r['isolation_fixes']<=256,'candidate_paths_checked':checked,'matrix_rows_checked':matrix_rows,'capacity_pairwise_sufficiency_checked':True,'status':r['status'],'complete_selection_verified':complete,'unsat_certified':False,'receipt_sha256':sha(out/'receipt.json'),'scope':'Independent original XML paths/exact1ns and every exported pair row checked; FOUND would include joint union/parents proof. Native search exhaustion/limit not an independently reconstructed exhaustive certificate; nativeFULL/STA and total benefit unproven.'},indent=2)+'\n');print('verified export',matrix_rows,'rows,',checked,'paths; status',r['status'],'complete',complete)
