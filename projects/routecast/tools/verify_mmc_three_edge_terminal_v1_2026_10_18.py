"""Full-NET candidate admission and exhaustive Hall on reported candidate graphs.

Candidate enumeration completeness is not certified by this verifier.
"""
import json,sys
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from criticality_net_admission_v1 import validate
from versioned_digest_cache_v1 import Cache

def main():
 d=R/'experiments/mmc_three_edge_terminal_probe_v1_2026-10-18'
 receipt=json.loads((d/'receipt.json').read_text())
 bindings={**receipt['bindings'],str(d/'receipt.json'):sha(d/'receipt.json'),**closure([Path(__file__)])}
 out=R/'experiments/mmc_three_edge_terminal_verification_v1_2026-10-18';out.mkdir()
 protocol=json.loads((d/'protocol.json').read_text());cache=Cache();summaries=[]
 with cache.installed():
  assert all(sha(p)==h for p,h in bindings.items())
  _,digest,_,f,rc,_=load_endpoints(protocol['inputs']['case_01']['endpoint'])
  for case,data in protocol['inputs'].items():
   frame=json.loads(Path(data['frame']).read_text());a=json.loads((d/(case+'.json')).read_text())
   original=json.loads((R/'experiments/mmc_terminal_assignment_probe_v1_2026-10-18'/(case+'.json')).read_text())
   assert frame['graph_sha256']==digest
   records={r['connection_id']:r for r in frame['records']}
   assert {c['sink_RR'] for c in a['classes']}=={c['sink_RR'] for c in original['classes']}
   capacities={c['sink_RR']:{int(p):n for p,n in c['available_IPIN_capacity'].items()} for c in original['classes']}
   selected={cid for c in a['classes'] for cid in c['connection_ids']};nets={records[cid]['net_id'] for cid in selected}
   groups=defaultdict(list)
   for r in frame['records']:
    if r['net_id'] in nets:groups[r['net_id']].append(r)
   needed={e for rs in groups.values() for r in rs for e in r['answer']['physical_edge_ids']}
   for c in a['classes']:
    for arm in c['arms'].values():
     for opts in arm['candidates'].values():
      for candidate in opts.values():needed.update(candidate['tail_edges'])
   slots={e:s for s,e in enumerate(f['edge_ids']) if e in needed};assert slots.keys()==needed
   queries={net:[{k:r[k] for k in ['connection_id','net_id','source','sink']} for r in rs] for net,rs in groups.items()}
   candidates_checked=0;subsets=0;feasible=Counter()
   for c in a['classes']:
    sink=c['sink_RR'];cap=capacities[sink]
    assert c['connection_ids']==sorted(r['connection_id'] for r in frame['records'] if r['sink']==sink)
    for depth,arm in c['arms'].items():
     rows={int(cid):{int(p):v for p,v in opts.items()} for cid,opts in arm['candidates'].items()}
     assert sorted(rows)==c['connection_ids']
     assert sum(map(len,rows.values()))==arm['candidate_pairs']
     for cid,opts in rows.items():
      r=records[cid];net=r['net_id']
      for pin,candidate in opts.items():
       tail=candidate['tail_edges'];assert len(tail)==int(depth)
       assert cap[pin]>0 and f['dest_ranks'][slots[tail[-2]]]==pin
       new=dict(r,answer=dict(status='FOUND',delay=candidate['delay'],physical_edge_ids=r['answer']['physical_edge_ids'][:-int(depth)]+tail))
       full=[new if sibling['connection_id']==cid else sibling for sibling in groups[net]]
       validate(f,rc,slots,queries[net],full)
       candidates_checked+=1
     keys=sorted(rows);deficit=0
     for mask in range(1<<len(keys)):
      subset=[cid for i,cid in enumerate(keys) if mask>>i&1]
      neighbors={p for cid in subset for p in rows[cid]}
      deficit=max(deficit,len(subset)-sum(cap[p] for p in neighbors));subsets+=1
     m=arm['matching'];assignment={int(cid):p for cid,p in m['matching'].items()}
     assert len(assignment)==m['matched']==len(keys)-deficit
     assert all(p in rows[cid] for cid,p in assignment.items())
     assert all(n<=cap[p] for p,n in Counter(assignment.values()).items())
     witness=m['hall_rows'];neighbors={p for cid in witness for p in rows[cid]}
     assert sorted(neighbors)==m['hall_resources'] and sum(cap[p] for p in neighbors)==m['hall_capacity']
     assert len(witness)-m['hall_capacity']==m['hall_deficit']==deficit
     assert m['feasible']==(deficit==0)
     feasible[depth]+=int(m['feasible'])
   summary=dict(case=case,full_NET_candidates_checked=candidates_checked,exhaustive_Hall_subsets=subsets,feasible_classes=dict(feasible))
   summaries.append(summary);print(json.dumps(summary),flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  with (out/'verification.json').open('x') as stream:
   json.dump(dict(status='pass',bindings=bindings,summaries=summaries,scope='Full-NET physical/single-parent/exact-RC/budget validation per individual reported candidate; exhaustive maximal matching and Hall witnesses on reported graphs. Enumeration completeness, combined assignments across classes, joint channel capacity and objective admission not certified.'),stream,indent=2)

if __name__=='__main__':main()
