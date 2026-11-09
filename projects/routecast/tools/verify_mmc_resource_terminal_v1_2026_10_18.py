"""Independent exhaustive Cartesian oracle using whole-NET ownership deltas."""
import json,sys,itertools
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from versioned_digest_cache_v1 import Cache

def main():
 d=R/'experiments/mmc_resource_constrained_terminal_v1_2026-10-18';receipt=json.loads((d/'receipt.json').read_text())
 bindings={**receipt['bindings'],str(d/'receipt.json'):sha(d/'receipt.json'),**closure([Path(__file__)])}
 protocol=json.loads((d/'protocol.json').read_text())
 out=R/'experiments/mmc_resource_terminal_verification_v1_2026-10-18';out.mkdir();summaries=[]
 cache=Cache()
 with cache.installed():
  assert all(sha(p)==h for p,h in bindings.items())
  _,digest,_,f,_,_=load_endpoints(protocol['inputs']['case_01']['endpoint'])
  for case,data in protocol['inputs'].items():
   frame=json.loads(Path(data['frame']).read_text());assert frame['graph_sha256']==digest
   produced=json.loads((d/(case+'.json')).read_text())
   candidate=json.loads((R/'experiments/mmc_three_edge_terminal_probe_v1_2026-10-18'/(case+'.json')).read_text())
   initial=json.loads((R/'experiments/mmc_terminal_assignment_probe_v1_2026-10-18'/(case+'.json')).read_text())
   pools={c['sink_RR']:set(map(int,c['available_IPIN_capacity'])) for c in initial['classes']}
   records={r['connection_id']:r for r in frame['records']};selected={cid for c in candidate['classes'] for cid in c['connection_ids']}
   nets={records[cid]['net_id'] for cid in selected};groups=defaultdict(list)
   for r in records.values():
    if r['net_id'] in nets:groups[r['net_id']].append(r)
   needed={e for rs in groups.values() for r in rs for e in r['answer']['physical_edge_ids']}
   for c in candidate['classes']:
    for opts in c['arms']['3']['candidates'].values():
     for item in opts.values():needed.update(item['tail_edges'])
   destinations={e:f['dest_ranks'][s] for s,e in enumerate(f['edge_ids']) if e in needed};assert destinations.keys()==needed
   ledger={int(p):n for p,n in frame['ledger'].items()};caps=f['capacities']
   def owned(rs):return {r['source'] for r in rs}|{destinations[e] for r in rs for e in r['answer']['physical_edge_ids']}
   old_owned={n:owned(rs) for n,rs in groups.items()};actual={c['sink_RR']:c for c in produced['classes']}
   combinations=0;feasible_classes=0
   for c in candidate['classes']:
    ids=c['connection_ids'];assert len({records[cid]['net_id'] for cid in ids})==len(ids)
    deltas={}
    for cid in ids:
     r=records[cid];net=r['net_id'];deltas[cid]={}
     for pin,item in c['arms']['3']['candidates'][str(cid)].items():
      new=dict(r,answer=dict(r['answer'],physical_edge_ids=r['answer']['physical_edge_ids'][:-3]+item['tail_edges']))
      new_owned=owned([new if s['connection_id']==cid else s for s in groups[net]])
      delta={p:1 for p in new_owned-old_owned[net]};delta.update({p:-1 for p in old_owned[net]-new_owned})
      deltas[cid][int(pin)]=delta
    answer=actual[c['sink_RR']]['resource_assignment'];reported={int(cid):pin for cid,pin in answer['assignment'].items()}
    any_feasible=False;reported_seen=False
    for values in itertools.product(*(sorted(deltas[cid]) for cid in ids)):
     combinations+=1;change=Counter()
     for cid,pin in zip(ids,values):change.update(deltas[cid][pin])
     feasible=all(ledger.get(p,0)+change[p]<=max(ledger.get(p,0),caps[p]) for p in change)
     feasible=feasible and all(ledger.get(p,0)+change[p]<=caps[p] for p in pools[c['sink_RR']])
     any_feasible|=feasible
     if dict(zip(ids,values))==reported:assert feasible;reported_seen=True
    assert any_feasible==answer['feasible']
    if any_feasible:assert reported_seen;feasible_classes+=1
   assert feasible_classes==produced['summary']['resource_feasible_classes']
   summary=dict(case=case,classes=len(candidate['classes']),exhaustive_combinations=combinations,resource_feasible_classes=feasible_classes)
   summaries.append(summary);print(json.dumps(summary),flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  with (out/'verification.json').open('x') as stream:json.dump(dict(status='pass',bindings=bindings,summaries=summaries,scope='Independent whole-NET ownership-delta Cartesian oracle for all reported depth3 class domains. Shared graph decoder, prior per-candidate path proof; no enumeration completeness, joint cross-class objective admission or native claim.'),stream,indent=2)

if __name__=='__main__':main()
