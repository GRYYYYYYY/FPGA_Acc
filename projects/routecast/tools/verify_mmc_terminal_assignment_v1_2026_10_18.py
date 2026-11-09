"""Independent candidate reconstruction and exhaustive Hall-subset verification.

Does not import the matching/proposal implementation. Physical graph and RC
decoder are shared trusted inputs; this is not an independent XML/RC decoder.
"""
import json, sys
from pathlib import Path
from bisect import bisect_right
from collections import Counter
R = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(R/'tools'), str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from versioned_digest_cache_v1 import Cache

def main():
 d=R/'experiments/mmc_terminal_assignment_probe_v1_2026-10-18'
 out=R/'experiments/mmc_terminal_assignment_verification_v1_2026-10-18'
 out.mkdir()
 receipt=json.loads((d/'receipt.json').read_text())
 bindings={**receipt['bindings'],str(d/'receipt.json'):sha(d/'receipt.json'),str(Path(__file__)):sha(__file__)}
 cache=Cache()
 with cache.installed():
  assert all(sha(p)==h for p,h in bindings.items())
  protocol=json.loads((d/'protocol.json').read_text())
  graph,digest,nodes,f,rc,_=load_endpoints(protocol['inputs']['case_01']['endpoint'])
  offsets=f['row_offsets']; dest=f['dest_ranks']; ids=f['edge_ids']; caps=f['capacities']
  kinds=[n.get('type') for n in nodes]
  pools={}; pin_sink={}
  for p,k in enumerate(kinds):
   if k!='IPIN':continue
   targets=set(dest[s] for s in range(offsets[p],offsets[p+1]))
   if len(targets)==1:
    t=next(iter(targets))
    if kinds[t]=='SINK' and offsets[t]==offsets[t+1]:
     pools.setdefault(t,[]).append(p);pin_sink[p]=t
  results=[]
  for case,data in protocol['inputs'].items():
   frame=json.loads(Path(data['frame']).read_text()); artifact=json.loads((d/(case+'.json')).read_text())
   assert frame['graph_sha256']==digest and frame['scale']==rc.scale
   ledger={int(k):v for k,v in frame['ledger'].items()}
   selected={pin_sink[p] for p,v in ledger.items() if v>caps[p] and kinds[p]=='IPIN' and p in pin_sink}
   assert {c['sink_RR'] for c in artifact['classes']}==selected
   records={r['connection_id']:r for r in frame['records']}
   needed={e for r in records.values() if r['sink'] in selected for e in r['answer']['physical_edge_ids'][-2:]}
   slots={e:s for s,e in enumerate(ids) if e in needed}; counts=Counter(); checked=0; subsets=0
   for c in artifact['classes']:
    sink=c['sink_RR']; rs=[r for r in records.values() if r['sink']==sink]
    assert sorted(r['connection_id'] for r in rs)==c['connection_ids']
    assert len({r['net_id'] for r in rs})==len(rs) and len(rs)<=caps[sink]
    assert all(caps[p]==1 for p in pools[sink])
    old=Counter(dest[slots[r['answer']['physical_edge_ids'][-2]]] for r in rs)
    available={p:max(0,caps[p]-(ledger.get(p,0)-old[p])) for p in pools[sink]}
    assert available=={int(p):v for p,v in c['available_IPIN_capacity'].items()}
    choices={}
    for r in rs:
     cid=r['connection_id']; path=r['answer']['physical_edge_ids']; a,b=[slots[e] for e in path[-2:]]
     u=bisect_right(offsets,a)-1
     assert pin_sink[dest[a]]==sink and offsets[dest[a]]<=b<offsets[dest[a]+1] and dest[b]==sink
     opts={}
     for s in range(offsets[u],offsets[u+1]):
      p=dest[s]
      if not available.get(p,0):continue
      for t in range(offsets[p],offsets[p+1]):
       assert dest[t]==sink
       delay=r['answer']['delay']-rc.increment(a)-rc.increment(b)+rc.increment(s)+rc.increment(t)
       candidate=(delay,[ids[s],ids[t]])
       if delay<=r['budget_integer'] and (p not in opts or candidate<opts[p]):opts[p]=candidate
     choices[cid]=opts
    assert sum(map(len,choices.values()))==c['candidate_edges']
    # Exhaust every subset, rather than rerun the producer's augmenting paths.
    rows=sorted(choices); maximum_deficit=0
    for mask in range(1<<len(rows)):
     neighbors=set(); size=0
     for i,cid in enumerate(rows):
      if mask>>i&1:size+=1;neighbors.update(choices[cid])
     maximum_deficit=max(maximum_deficit,size-sum(available[p] for p in neighbors));subsets+=1
    m=c['matching']; assert m['matched']==len(rows)-maximum_deficit
    assignment={int(cid):p for cid,p in m['matching'].items()}
    assert len(assignment)==m['matched'] and all(p in choices[cid] for cid,p in assignment.items())
    assert all(n<=available[p] for p,n in Counter(assignment.values()).items())
    witness=m['hall_rows']; neighbors=set(p for cid in witness for p in choices[cid])
    assert sorted(neighbors)==m['hall_resources']
    assert sum(available[p] for p in neighbors)==m['hall_capacity']
    assert len(witness)-m['hall_capacity']==m['hall_deficit']==maximum_deficit
    feasible=maximum_deficit==0
    assert m['feasible']==feasible
    assert c['status']==('FEASIBLE_PREFIX_BUDGET_PROPOSAL' if feasible else 'HALL_DEFICIENT_PREFIX_BUDGET_GRAPH')
    assert len(c['assignments'])==(len(rows) if feasible else 0)
    for a in c['assignments']:
     cid=a['connection_id'];r=records[cid];p=assignment[cid];delay,tail=choices[cid][p]
     assert a['physical_edge_ids']==r['answer']['physical_edge_ids'][:-2]+tail
     assert a['candidate_delay']==delay==rc.path(r['source'],sink,a['physical_edge_ids'])<=r['budget_integer']
     assert a['budget_integer']==r['budget_integer'] and a['new_IPIN']==p
     checked+=1
    counts[c['status']]+=1
   result=dict(case=case,classes=len(selected),statuses=dict(counts),verified_proposals=checked,exhaustive_Hall_subsets=subsets)
   results.append(result);print(json.dumps(result),flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  with (out/'verification.json').open('x') as stream:
   json.dump(dict(status='pass',bindings=bindings,cases=results,scope='Independent candidate enumeration and exhaustive Hall subsets; shared physical graph/RC decoder. No objective admission, atomic update, native legality, channel quality or full-flow gain certified.',digest=cache.snapshot()),stream,indent=2)
 print('ALL3 TERMINAL CANDIDATES AND EXHAUSTIVE HALL VERIFIED',flush=True)

if __name__=='__main__':main()
