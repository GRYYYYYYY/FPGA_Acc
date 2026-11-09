"""Separate physical adjacency and budget restrictions without changing a frame."""
import json,sys
from pathlib import Path
from bisect import bisect_right
from collections import Counter
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from versioned_digest_cache_v1 import Cache

def deficiency(rows,capacity):
 ids=sorted(rows);best=0;witness=[]
 for mask in range(1<<len(ids)):
  subset=[cid for i,cid in enumerate(ids) if mask>>i&1]
  neighbors={p for cid in subset for p in rows[cid]}
  deficit=len(subset)-sum(capacity[p] for p in neighbors)
  if deficit>best:best=deficit;witness=subset
 return best,witness

def main():
 source=R/'experiments/mmc_terminal_assignment_probe_v1_2026-10-18'
 proof=R/'experiments/mmc_terminal_assignment_verification_v1_2026-10-18/verification.json'
 v=json.loads(proof.read_text());assert v['status']=='pass'
 bindings={**v['bindings'],str(proof):sha(proof),str(Path(__file__)):sha(__file__)}
 out=R/'experiments/mmc_terminal_prefix_limits_v1_2026-10-18';out.mkdir()
 protocol=json.loads((source/'protocol.json').read_text())
 with (out/'protocol.json').open('x') as stream:
  json.dump(dict(bindings=bindings,selection='All49 originally selected pre-route pressure classes. No native labels.',comparison='Same upstream and terminal physical edges; compare original-budget candidates with physical adjacency ignoring only budget. The latter is a diagnostic upper bound, never a proposed budget relaxation.',scope='No state mutation or model admission. Exhaustive Hall subsets; shared graph and RC decoder.'),stream,indent=2)
 cache=Cache();summaries=[]
 with cache.installed():
  assert all(sha(p)==h for p,h in bindings.items())
  _,digest,nodes,f,rc,_=load_endpoints(protocol['inputs']['case_01']['endpoint'])
  offsets=f['row_offsets'];dest=f['dest_ranks'];edges=f['edge_ids']
  for case,data in protocol['inputs'].items():
   frame=json.loads(Path(data['frame']).read_text());artifact=json.loads((source/(case+'.json')).read_text())
   assert frame['graph_sha256']==digest
   sinks={c['sink_RR'] for c in artifact['classes']}
   groups={s:[] for s in sinks}
   for r in frame['records']:
    if r['sink'] in sinks:groups[r['sink']].append(r)
   needed={e for rs in groups.values() for r in rs for e in r['answer']['physical_edge_ids'][-2:]}
   slots={e:i for i,e in enumerate(edges) if e in needed};results=[];counts=Counter()
   for c in artifact['classes']:
    sink=c['sink_RR'];capacity={int(p):n for p,n in c['available_IPIN_capacity'].items()}
    physical={};budgeted={};excluded=[]
    for r in groups[sink]:
     cid=r['connection_id'];a,b=[slots[e] for e in r['answer']['physical_edge_ids'][-2:]]
     upstream=bisect_right(offsets,a)-1;choices={}
     for x in range(offsets[upstream],offsets[upstream+1]):
      p=dest[x]
      if not capacity.get(p,0):continue
      for y in range(offsets[p],offsets[p+1]):
       assert dest[y]==sink
       delay=r['answer']['delay']-rc.increment(a)-rc.increment(b)+rc.increment(x)+rc.increment(y)
       choices[p]=min(choices.get(p,delay),delay)
     physical[cid]=set(choices)
     budgeted[cid]={p for p,delay in choices.items() if delay<=r['budget_integer']}
     excluded.extend(dict(connection_id=cid,IPIN=p,budget_excess_integer=delay-r['budget_integer']) for p,delay in choices.items() if delay>r['budget_integer'])
    dp,wp=deficiency(physical,capacity);db,wb=deficiency(budgeted,capacity)
    assert db==c['matching']['hall_deficit'] and dp<=db
    label='already_feasible' if db==0 else ('physical_adjacency_deficient' if dp else 'budget_only_deficient')
    counts[label]+=1
    results.append(dict(sink_RR=sink,classification=label,physical_deficit=dp,budgeted_deficit=db,physical_witness=wp,budgeted_witness=wb,physical_candidate_pairs=sum(map(len,physical.values())),budgeted_candidate_pairs=sum(map(len,budgeted.values())),budget_exclusions=excluded))
   summary=dict(case=case,classes=len(results),classification=dict(counts),physical_deficit_sum=sum(r['physical_deficit'] for r in results),budgeted_deficit_sum=sum(r['budgeted_deficit'] for r in results),budget_excluded_pairs=sum(len(r['budget_exclusions']) for r in results))
   with (out/(case+'.json')).open('x') as stream:json.dump(dict(summary=summary,classes=results),stream,indent=2)
   summaries.append(summary);print(json.dumps(summary),flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  bindings.update({str(p):sha(p) for p in out.glob('*.json')})
  with (out/'diagnosis.json').open('x') as stream:json.dump(dict(status='complete',bindings=bindings,summaries=summaries,scope='Physical-only relaxed-budget graph is diagnostic, not admitted; no global infeasibility or quality/utility claim.'),stream,indent=2)

if __name__=='__main__':main()
