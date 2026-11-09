"""One bounded resource-derived blocker release, preserving original1ns constraint."""
import json
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction
from pre_route_endpoints import sha
from nonzero_rc_search_context import load
from native_capacity_rc_search import NativeCapacityRC
root=Path(__file__).resolve().parents[1];parent=root/'experiments/nonzero_rc_joint_integer_search_2026-10-06';pr=json.loads((parent/'receipt.json').read_text());proof=json.loads((parent/'verification.json').read_text());assert sha(parent/'receipt.json')==proof['receipt_sha256'];diagnosis=root/'experiments/nonzero_rc_joint_failure_diagnosis_v2_2026-10-06';d=json.loads((diagnosis/'receipt.json').read_text());dv=json.loads((diagnosis/'verification.json').read_text());assert sha(diagnosis/'receipt.json')==dv['receipt_sha256'];graph,digest,nodes,f,rc,queries,_=load(root);assert digest==pr['graph_sha256']==d['graph_sha256'];failed=d['failed_query'];blockers=sorted({net for b in d['unoccupied_shortest_path_blockers'] for net in b['owner_nets']});assert blockers==[11,36];slots={f['edge_ids'][i]:(u,f['dest_ranks'][i]) for u in range(len(nodes)) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])};unions=defaultdict(set);ledger=Counter();arcs=defaultdict(set);records=[]
def add(row):
 net=row['net_id'];used={row['source']};node=row['source']
 for eid in row['result']['physical_edge_ids']:u,v=slots[eid];assert u==node;node=v;used.add(node);arcs[net].add((u,v,eid))
 assert node==row['sink'];ledger.update(used-unions[net]);unions[net].update(used);records.append(row)
for row in pr['results'][:-1]:
 if row['net_id'] not in blockers:add({**row,'origin':'RETAINED'})
key=lambda q:(q['net_id'],q['pin_index']);cut=next(i for i,q in enumerate(queries) if key(q)==key(failed));queue=[queries[cut]]+[q for q in queries[:cut] if q['net_id'] in blockers]+queries[cut+1:];native=NativeCapacityRC(rc);budget=(Fraction(1,10**9)*rc.scale).__floor__();failure=None
for q in queue:
 other=Counter(ledger)
 for n in unions[q['net_id']]:other[n]-=1
 native.set_other(dict(+other));answer=native.query(q['source'],q['sink'],budget,max_labels=10000);row={**q,'result':answer,'origin':'REPAIRED','other_before':dict(+other)}
 if answer['status']!='FOUND':failure=row;break
 add(row)
parents=defaultdict(set)
for net,edges in arcs.items():
 for u,v,eid in edges:parents[(net,v)].add((u,eid))
bad=[{'net':net,'node':n,'parents':len(p)} for (net,n),p in parents.items() if len(p)>1];overflow={n:v-f['capacities'][n] for n,v in ledger.items() if v>f['capacities'][n]};out=root/'experiments/nonzero_rc_blocker_repair_2026-10-06';out.mkdir();result={'records':records,'failure':failure,'required_connections':len(queries),'completed_connections':len(records),'blocker_nets':blockers,'queue':[key(q) for q in queue],'multi_parent_nodes':bad,'overflow_nodes':overflow,'budget_integer':budget,'scale':rc.scale,'graph_sha256':digest,'parent_verification_sha256':sha(parent/'verification.json'),'diagnosis_verification_sha256':sha(diagnosis/'verification.json'),'source_sha256':sha(Path(__file__)),'scope':'One attempt: resource blockers from unoccupied shortest path in failed frozen state, release blocker NET unions, route failed connection then blockers then remainder, fixed1ns/10000 labels. Staged diagnostic only; partial result never published. No native residual/nonconfigurable/FULL/STA certification.'};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print('completed',len(records),'of',len(queries),'failure',failure and failure['result']['status'],'overflow',sum(overflow.values()),'multi-parent',len(bad))
