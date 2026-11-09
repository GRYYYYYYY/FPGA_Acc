"""Independently verify XML witnesses and every elimination/branch certificate."""
import json
from pathlib import Path
from fractions import Fraction
from collections import defaultdict
from pre_route_endpoints import sha
from nonzero_rc_search_context import load
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];out=root/'experiments/nonzero_rc_degree_selection_2026-10-06';parent=root/'experiments/nonzero_rc_multi_context_2026-10-06'
r=json.loads((out/'receipt.json').read_text());pool=json.loads((parent/'receipt.json').read_text());assert r['parent_receipt_sha256']==sha(parent/'receipt.json') and r['source_sha256']==sha(root/'tools/trial_nonzero_rc_degree_selection.py') and r['protocol_sha256']==sha(out/'protocol.json')
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
states=0;removed=0;leaves=defaultdict(int);found=None

def check(proof,domains):
 global states,removed,found
 if 'limit' in proof:assert proof=={'limit':True};leaves['limit']+=1;return
 states+=1
 for i,a,j in proof['removals']:
  assert i!=j and a in domains[i] and all(not compatible(i,a,j,b) for b in domains[j]);domains[i].remove(a);removed+=1
 if 'empty' in proof:assert not domains[proof['empty']];leaves['empty']+=1;return
 assert all(domains)
 if 'capacity_dead' in proof or 'solution' in proof:
  assert all(len(d)==1 for d in domains);selected=[next(iter(d)) for d in domains];owners=defaultdict(set);parents=defaultdict(set)
  for i,a in enumerate(selected):
   for n in foot[i][a]:owners[n].add(keys[i][0])
   for n,v in incoming[i][a].items():parents[(keys[i][0],n)].add(v)
  feasible=all(len(v)<=audit.caps[n] for n,v in owners.items()) and all(len(v)==1 for v in parents.values())
  if 'solution' in proof:assert feasible and proof['solution']==selected;found=selected;leaves['solution']+=1
  else:assert not feasible;leaves['capacity_dead']+=1
  return
 i=proof['branch'];assert len(domains[i])>1;options=sorted(domains[i]);visited=[c['candidate'] for c in proof['children']]
 assert visited==options[:len(visited)]
 for child in proof['children']:
  ds=[set(d) for d in domains];ds[i]={child['candidate']};check(child['proof'],ds)
 if len(visited)!=len(options):assert found is not None or leaves['limit']
check(r['proof'],[set(range(len(ps))) for ps in paths]);assert states==r['states'] and removed==r['pruned_candidates']
if r['status']=='CANDIDATE_SET_UNSAT':assert found is None and not leaves['limit']
elif r['status']=='COMPLETE_DIAGNOSTIC':assert found==r['selected']
else:assert r['status']=='SELECTION_LIMIT' and leaves['limit'] and found is None
(out/'verification.json').write_text(json.dumps({'status':r['status'],'candidate_paths_checked':checked,'proof_states_checked':states,'eliminations_checked':removed,'leaves':dict(leaves),'finite_pool_unsat_certified':r['status']=='CANDIDATE_SET_UNSAT','complete_selection':found,'receipt_sha256':sha(out/'receipt.json'),'scope':'Original XML exact1ns paths and independent pairwise elimination/branch certificate; full graph feasibility remains separate; no native FULL/STA or performance claim.'},indent=2)+'\n');print('verified',r['status'],states,'states',removed,'eliminations')
