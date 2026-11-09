"""Frozen four candidates per connection and bounded pure-Python joint selection."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from pre_route_endpoints import sha
from nonzero_rc_search_context import load
from native_capacity_rc_search import NativeCapacityRC
root=Path(__file__).resolve().parents[1];out=root/'experiments/nonzero_rc_resource_avoidance_2026-10-06';out.mkdir();parent=root/'experiments/nonzero_rc_fanout_observable64_2026-10-06';r=json.loads((parent/'receipt.json').read_text());v=json.loads((parent/'verification.json').read_text());assert sha(parent/'receipt.json')==v['receipt_sha256'] and all(sha(p)==h for p,h in r['files_sha256'].items());graph,digest,nodes,f,rc,queries,_=load(root);budget=(Fraction(1,10**9)*rc.scale).__floor__();(out/'protocol.json').write_text(json.dumps({'candidates_per_connection':12,'additional_avoidance_queries':8,'selection_state_limit':10000,'budget_integer':budget,'max_labels':10000,'diversity':'Reuse prior generated candidates; forbid each of top8 most shared internal nodes separately using hard capacity, exact delay costs; no native reference paths.','selection':'Dynamic fewest compatible candidates, NET/pin tie; enforce per-NET union capacity and unique incoming parent','graph_sha256':digest},indent=2)+'\n');slots={f['edge_ids'][i]:(u,f['dest_ranks'][i]) for u in range(len(nodes)) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])};native=NativeCapacityRC(rc);native.set_other({});candidates={};attempts=[]
# Seed with independently generated paths, never native reference paths.
prior=json.loads((root/'experiments/nonzero_rc_candidate_joint_selection_2026-10-06/receipt.json').read_text())
prior_paths={tuple(g['key']):g['paths'] for g in prior['candidates']}
popularity=Counter(n for g in prior['candidates'] for n in set(n for p in g['paths'] for n in p['nodes']))
for q in queries:
 key=(q['net_id'],q['pin_index']);paths=list(prior_paths[key]);unique={tuple(p['answer']['physical_edge_ids']) for p in paths}
 resources=set(n for p in paths for n in p['nodes'])-{q['source'],q['sink']}
 targets=sorted(resources,key=lambda n:(-popularity[n],n))[:8]
 for attempt,blocked in enumerate(targets):
  native.set_other({blocked:f['capacities'][blocked]})
  for i in range(len(f['dest_ranks'])):native.arrays[3][i]=rc.increments[i]
  answer=native.query(q['source'],q['sink'],budget,max_labels=10000);attempts.append({'key':list(key),'attempt':attempt,'blocked_node':blocked,'status':answer['status']})
  if answer['status']!='FOUND':continue
  node=q['source'];used={node};parents=[]
  for eid in answer['physical_edge_ids']:u,dst=slots[eid];assert node==u;node=dst;used.add(node);parents.append((dst,u,eid))
  assert node==q['sink'] and blocked not in used;signature=tuple(answer['physical_edge_ids'])
  if signature not in unique:paths.append({'answer':answer,'nodes':sorted(used),'parents':parents});unique.add(signature)
 candidates[key]=paths
use=Counter();occupancy=Counter();parents=defaultdict(Counter);chosen={};states=0;limited=False
qmap={(q['net_id'],q['pin_index']):q for q in queries}
def compatible(key,c):
 net=key[0]
 return all(use[(net,n)] or occupancy[n]<f['capacities'][n] for n in c['nodes']) and all(not parents[(net,n)] or (u,eid) in parents[(net,n)] for n,u,eid in c['parents'])
def apply(key,c,sign):
 net=key[0]
 for n in c['nodes']:
  old=use[(net,n)];use[(net,n)]+=sign
  if old==0 and sign==1:occupancy[n]+=1
  if use[(net,n)]==0 and sign==-1:occupancy[n]-=1
 for n,u,eid in c['parents']:
  p=parents[(net,n)];p[(u,eid)]+=sign
  if p[(u,eid)]==0:del p[(u,eid)]
def search():
 global states,limited
 if len(chosen)==len(queries):return True
 if states>=10000:limited=True;return False
 states+=1;best=None;options=None
 for key in sorted(candidates):
  if key in chosen:continue
  possible=[i for i,c in enumerate(candidates[key]) if compatible(key,c)]
  if not possible:return False
  if options is None or len(possible)<len(options):best,options=key,possible
 for index in options:
  c=candidates[best][index];apply(best,c,1);chosen[best]=index
  if search():return True
  del chosen[best];apply(best,c,-1)
  if limited:return False
 return False
success=search();records=[{**qmap[key],'result':candidates[key][index]['answer']} for key,index in sorted(chosen.items())];result={'status':'COMPLETE_DIAGNOSTIC' if success else 'SELECTION_LIMIT' if limited else 'CANDIDATE_SET_UNSAT','records':records,'required_connections':len(queries),'completed_connections':len(records),'selection_states':states,'candidates':[{'key':list(k),'paths':p} for k,p in sorted(candidates.items())],'attempts':attempts,'graph_sha256':digest,'scale':rc.scale,'budget_integer':budget,'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__)),'scope':'Finite generated path set only; exact1ns constraints and joint NET/node capacity/unique parents. UNSAT pertains only to this candidate set, not full graph. No native reference path copying, residual OPIN/closure/FULL/STA or performance/generalization proof.'};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],len(records),'of',len(queries),'states',states,'candidates',sum(len(p) for p in candidates.values()))
