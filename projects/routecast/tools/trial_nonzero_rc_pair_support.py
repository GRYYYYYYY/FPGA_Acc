"""Generate alternatives under pair conflicts certified by AC propagation."""
import json
from pathlib import Path
from collections import defaultdict
from fractions import Fraction
from pre_route_endpoints import sha
from nonzero_rc_search_context import load
from native_capacity_rc_search import NativeCapacityRC
root=Path(__file__).resolve().parents[1];parent=root/'experiments/nonzero_rc_conflict_context_2026-10-06';proofdir=root/'experiments/nonzero_rc_arc_consistency_2026-10-06';out=root/'experiments/nonzero_rc_pair_support_2026-10-06';out.mkdir()
r=json.loads((parent/'receipt.json').read_text());proof=json.loads((proofdir/'receipt.json').read_text());verified=json.loads((proofdir/'verification.json').read_text());assert verified['receipt_sha256']==sha(proofdir/'receipt.json') and proof['parent_receipt_sha256']==sha(parent/'receipt.json')
graph,digest,nodes,f,rc,queries,_=load(root);keys=[tuple(g['key']) for g in r['candidates']];paths=[g['paths'] for g in r['candidates']];qmap={(q['net_id'],q['pin_index']):q for q in queries};contexts=defaultdict(list);seen=defaultdict(set)
(out/'protocol.json').write_text(json.dumps({'pool_sha256':sha(parent/'receipt.json'),'proof_sha256':sha(proofdir/'receipt.json'),'contexts_per_connection':8,'budget_ns':1,'max_labels':10000,'policy':'Depth-first AC removal order: search target connection under each distinct other-NET surviving supporter candidate occupancy, first8 per connection; exact delay cost; same-NET contexts excluded; no reference paths'},indent=2)+'\n')
def collect(p,domains):
 for i,a,j in p['removals']:
  if keys[i][0]!=keys[j][0]:
   for b in sorted(domains[j]):
    if (j,b) not in seen[i] and len(contexts[i])<8:contexts[i].append((j,b));seen[i].add((j,b))
  domains[i].remove(a)
 if 'branch' in p:
  i=p['branch']
  for c in p['children']:
   ds=[set(d) for d in domains];ds[i]={c['candidate']};collect(c['proof'],ds)
collect(proof['proof'],[set(range(len(ps))) for ps in paths]);native=NativeCapacityRC(rc);slots={f['edge_ids'][slot]:(u,f['dest_ranks'][slot]) for u in range(len(nodes)) for slot in range(f['row_offsets'][u],f['row_offsets'][u+1])};budget=(Fraction(1,10**9)*rc.scale).__floor__();attempts=[];candidates=[]
for slot in range(len(f['dest_ranks'])):native.arrays[3][slot]=rc.increments[slot]
for i,key in enumerate(keys):
 q=qmap[key];result=list(paths[i]);signatures={tuple(p['answer']['physical_edge_ids']) for p in result}
 for j,b in contexts[i]:
  other={n:1 for n in paths[j][b]['nodes']};native.set_other(other);answer=native.query(q['source'],q['sink'],budget,max_labels=10000);attempts.append({'key':list(key),'support_key':list(keys[j]),'support_candidate':b,'answer':answer})
  if answer['status']!='FOUND':continue
  node=q['source'];used={node};parents=[]
  for eid in answer['physical_edge_ids']:u,node2=slots[eid];assert node==u;node=node2;used.add(node);parents.append([node,u,eid])
  assert node==q['sink'];signature=tuple(answer['physical_edge_ids'])
  if signature not in signatures:result.append({'answer':answer,'nodes':sorted(used),'parents':parents});signatures.add(signature)
 candidates.append({'key':list(key),'paths':result})
receipt={'status':'GENERATED_NOT_SELECTED','candidates':candidates,'attempts':attempts,'graph_sha256':digest,'scale':rc.scale,'pool_sha256':sha(parent/'receipt.json'),'proof_sha256':sha(proofdir/'receipt.json'),'source_sha256':sha(Path(__file__)),'protocol_sha256':sha(out/'protocol.json')};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('candidates',sum(len(c['paths']) for c in candidates),'attempts',len(attempts),'found',sum(a['answer']['status']=='FOUND' for a in attempts))
