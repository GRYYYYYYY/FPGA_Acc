"""Independent raw XML ownership, exhaustive detour options and greedy selection."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction as F
from immutable_xml_prediction_audit import ImmutableXMLAudit
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_owner_union_wire_fixed_cap_cohort_2026-10-07';protocol=json.loads((out/'protocol.json').read_text());last=None
for case in protocol['cases']:
 w,i=case['width'],case['index'];file=out/f'w{w}_m{i}/result.json'
 if not file.exists():continue
 d=json.loads(file.read_text());ep=json.loads(Path(case['target']).read_text())
 if last!=w:xml=ImmutableXMLAudit(ep['inputs']['graph']['path'],ep['graph_sha256']);last=w
 trace=d['result']['trace'];allocations=d['allocations'];cursor=1;sequence=1;decisions=0;dropped=0
 def score(s):return (F(s['floor_cpd_ns']),F(s['total_floor_increase_ns']))
 def key(r):return tuple((int(k),tuple(v)) for k,v in sorted(r.items(),key=lambda x:int(x[0])))
 def snapshot():return [dict(depth=x[0],score=[str(v) for v in x[1]],order=x[2],parent=x[5],restrictions=x[3],allocation_index=x[4]) for x in sorted(queue,key=lambda x:x[:3])]
 queue=[(0,score(allocations[0]),0,{},0,None)];seen={key({})}
 for j,entry in enumerate(trace):
  assert entry['queue_before']==snapshot();queue.sort(key=lambda x:x[:3]);depth,value,order,r,index,parent=queue.pop(0)
  assert entry['depth']==depth and entry['parent']==parent and entry['queue_order']==order and entry['restrictions']==r and d['attempts'][j]['allocation_index']==index
  candidate=entry['candidate'];restriction={int(k):set(v) for k,v in r.items()};expected=[]
  if 'observation' not in entry:assert j==len(trace)-1;continue
  observation=entry['observation']
  if observation['status']=='OBSERVED_CONFLICT':
   q=candidate['failure']['query'];assert observation['query']==q;unions=defaultdict(set)
   for record in candidate['records']:
    unions[record['net_id']].add(record['source'])
    for eid in record['answer']['physical_edge_ids']:edge=xml.graph.edges[eid];unions[record['net_id']].update((edge.source,edge.sink))
   ledger=Counter(node for union in unions.values() for node in union);assert ledger==Counter({int(k):v for k,v in candidate['ledger'].items()});blockers=[]
   for node in observation['witness']['path_nodes']:
    demand=ledger.get(node,0)-int(node in unions[q['net_id']]);owners=sorted(net for net,union in unions.items() if net!=q['net_id'] and node in union)
    if demand>=xml.caps[node] and owners:blockers.append(dict(node=node,owners=owners))
   assert blockers==observation['blockers'];assert observation['witness']['minimum'] is not None
   spec=allocations[d['attempts'][j]['allocation_index']];budget=min(int(F(spec['budgets_ns'][str(q['connection_id'])])*candidate['scale']/10**9),candidate['scale']//10**9);assert observation['witness']['minimum']<=budget
   for blocker in blockers:
    for net in sorted({q['net_id'],*blocker['owners']}):
     proposed={k:set(v) for k,v in restriction.items()};proposed.setdefault(net,set()).add(blocker['node'])
     if proposed==restriction or len(proposed)>16 or sum(map(len,proposed.values()))>32:continue
     canonical={str(k):sorted(v) for k,v in proposed.items()}
     if canonical not in expected:expected.append(canonical)
  assert [o['restrictions'] for o in entry['options']]==expected;evictions=[]
  for option in entry['options']:
   proposed=option['restrictions'];identity=key(proposed)
   if identity in seen:assert option['status']=='DUPLICATE';continue
   seen.add(identity);spec=allocations[cursor];assert spec['index']==cursor and spec['restrictions']==proposed;seed=allocations[0]['floor_ns'];increase=sum(max(F(0),F(v)-F(seed[c])) for c,v in spec['floor_ns'].items());assert increase==F(spec['total_floor_increase_ns'])
   if spec['valid']:
    assert option['status']=='QUEUED';queue.append((depth+1,score(spec),sequence,proposed,cursor,j));sequence+=1
    if len(queue)>32:
     worst=max(range(len(queue)),key=lambda n:queue[n][:3]);evictions.append(queue.pop(worst)[2]);dropped+=1
   else:assert option['status']=='ALLOCATION_REJECTED'
   cursor+=1;decisions+=1
  assert entry['frontier_evictions']==evictions and entry['queue_after']==snapshot()
 assert cursor==len(allocations) and dropped==d['result']['dropped_frontier']
 if d['result']['status']=='FRONTIER_EXHAUSTED':assert not queue
 if d['result']['status']=='ATTEMPT_LIMIT':assert len(trace)==4
 (file.parent/'choice_verification.json').write_text(json.dumps(dict(result_sha256=sha(file),verifier_sha256=sha(Path(__file__)),option_decisions=decisions,scope='Independent XML owner/options and exact breadth-first score/order queue replay, global dedup, allocation provenance, parent selection and frontier evictions. Native acceptance separate.'),indent=2)+'\n');print(w,i,'verified branch choices',decisions,flush=True)
