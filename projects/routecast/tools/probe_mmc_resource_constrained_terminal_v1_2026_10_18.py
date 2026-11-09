"""Exact per-class resource-constrained matching on frozen reported domains."""
import json,sys
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from criticality_net_admission_v1 import validate
from terminal_resource_assignment_v1 import solve
from versioned_digest_cache_v1 import Cache

def main():
 source=R/'experiments/mmc_three_edge_terminal_probe_v1_2026-10-18'
 proof=R/'experiments/mmc_three_edge_terminal_verification_v1_2026-10-18/verification.json'
 core=R/'experiments/terminal_resource_assignment_core_v1_2026-10-18/verification.json'
 v=json.loads(proof.read_text());cv=json.loads(core.read_text());assert v['status']==cv['status']=='pass'
 bindings={**v['bindings'],**cv['bindings'],str(proof):sha(proof),str(core):sha(core),**closure([Path(__file__)])}
 protocol=json.loads((source/'protocol.json').read_text())
 out=R/'experiments/mmc_resource_constrained_terminal_v1_2026-10-18';out.mkdir()
 with (out/'protocol.json').open('x') as stream:
  json.dump(dict(bindings=bindings,inputs=protocol['inputs'],selection='All49 frozen initial classes and reported depth3 candidates. No native labels or outcome selection.',constraints='Exactly one candidate per query; selected class IPIN occupancy <= original capacity; every other node occupancy <= max(original occupancy, original capacity). Same unchanged sibling and prefix ownership retained. Exact deterministic finite-domain search, no state/time cutoff.',scope='Per-class feasibility only, then diagnose all feasible class union. Original budgets fixed; no objective admission/model commit or native gain. Domain completeness not independently certified.'),stream,indent=2)
 cache=Cache();summaries=[]
 with cache.installed():
  assert all(sha(p)==h for p,h in bindings.items())
  _,digest,nodes,f,rc,_=load_endpoints(protocol['inputs']['case_01']['endpoint'])
  kinds=[n.get('type') for n in nodes];caps=f['capacities']
  for case,data in protocol['inputs'].items():
   frame=json.loads(Path(data['frame']).read_text());artifact=json.loads((source/(case+'.json')).read_text())
   initial=json.loads((R/'experiments/mmc_terminal_assignment_probe_v1_2026-10-18'/(case+'.json')).read_text())
   pools={c['sink_RR']:set(map(int,c['available_IPIN_capacity'])) for c in initial['classes']}
   assert frame['graph_sha256']==digest
   records={r['connection_id']:r for r in frame['records']};ledger={int(p):n for p,n in frame['ledger'].items()}
   selected={cid for c in artifact['classes'] for cid in c['connection_ids']};touched={records[cid]['net_id'] for cid in selected};groups=defaultdict(list)
   for r in records.values():
    if r['net_id'] in touched:groups[r['net_id']].append(r)
   needed={e for rs in groups.values() for r in rs for e in r['answer']['physical_edge_ids']}
   for c in artifact['classes']:
    for opts in c['arms']['3']['candidates'].values():
     for item in opts.values():needed.update(item['tail_edges'])
   slots={e:s for s,e in enumerate(f['edge_ids']) if e in needed};assert slots.keys()==needed
   queries={n:[{k:r[k] for k in ['connection_id','net_id','source','sink']} for r in rs] for n,rs in groups.items()}
   old_owned={n:validate(f,rc,slots,queries[n],rs)['owned'] for n,rs in groups.items()}
   def evaluate(replacements):
    changes=Counter();errors=[]
    for net in {r['net_id'] for r in replacements.values()}:
     rs=[replacements.get(r['connection_id'],r) for r in groups[net]]
     try:owned=validate(f,rc,slots,queries[net],rs)['owned']
     except ValueError as error:errors.append(dict(net_id=net,reason=str(error)));continue
     for p in owned-old_owned[net]:changes[p]+=1
     for p in old_owned[net]-owned:changes[p]-=1
    if errors:return dict(tree_errors=errors)
    after=Counter();before=Counter();increased=[]
    for p in ledger.keys()|changes.keys():
     old=ledger.get(p,0);new=old+changes[p];assert new>=0
     before[kinds[p]]+=max(0,old-caps[p]);after[kinds[p]]+=max(0,new-caps[p])
     if new>max(old,caps[p]):increased.append(p)
    return dict(tree_errors=[],old_overflow=dict(before),new_overflow=dict(after),nodes_increasing_overflow=sorted(increased),changed_queries=sum(r['answer']!=records[cid]['answer'] for cid,r in replacements.items()))
   results=[];union={};feasible_count=0
   for c in artifact['classes']:
    sink=c['sink_RR'];cids=c['connection_ids'];assert len({records[cid]['net_id'] for cid in cids})==len(cids)
    background=dict(ledger);fixed={};options={};candidates={}
    for cid in cids:
     r=records[cid];net=r['net_id'];owned={r['source']}
     for sibling in groups[net]:
      edges=sibling['answer']['physical_edge_ids'] if sibling['connection_id']!=cid else sibling['answer']['physical_edge_ids'][:-3]
      owned.update(f['dest_ranks'][slots[e]] for e in edges)
     assert owned<=old_owned[net];fixed[cid]=owned
     for p in old_owned[net]-owned:background[p]-=1
    for cid in cids:
     options[cid]={};candidates[cid]={};r=records[cid]
     for pin,item in c['arms']['3']['candidates'][str(cid)].items():
      pin=int(pin);path=r['answer']['physical_edge_ids'][:-3]+item['tail_edges']
      consumption={f['dest_ranks'][slots[e]] for e in item['tail_edges']}-fixed[cid]
      options[cid][pin]=consumption
      candidates[cid][pin]=dict(r,answer=dict(status='FOUND',delay=item['delay'],physical_edge_ids=path))
    resource_set={p for opts in options.values() for rs in opts.values() for p in rs}|pools[sink]
    bounds={p:(caps[p] if p in pools[sink] else max(caps[p],ledger.get(p,0)))-background.get(p,0) for p in resource_set}
    if any(n<0 for n in bounds.values()):answer=dict(feasible=False,assignment={},reason='fixed_background_exceeds_bound')
    else:answer=solve(options,bounds)
    result=dict(sink_RR=sink,resource_assignment=answer,connection_ids=cids)
    if answer['feasible']:
     chosen={cid:candidates[cid][pin] for cid,pin in answer['assignment'].items()}
     audit=evaluate(chosen);assert not audit['tree_errors'] and not audit['nodes_increasing_overflow']
     assert all(ledger.get(p,0)+sum(int(p in options[cid][pin]) for cid,pin in answer['assignment'].items())-(ledger.get(p,0)-background.get(p,0))<=caps[p] for p in pools[sink])
     result['audit']=audit;result['replacements']=list(chosen.values());union.update(chosen);feasible_count+=1
    results.append(result)
   union_audit=evaluate(union)
   summary=dict(case=case,classes=len(results),resource_feasible_classes=feasible_count,pin_only_feasible_classes=sum(c['arms']['3']['matching']['feasible'] for c in artifact['classes']),all_feasible_union_audit=union_audit)
   with (out/(case+'.json')).open('x') as stream:json.dump(dict(summary=summary,classes=results),stream,indent=2)
   summaries.append(summary);print(json.dumps(summary),flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  bindings.update({str(p):sha(p) for p in out.glob('*.json')})
  with (out/'receipt.json').open('x') as stream:json.dump(dict(status='resource_proposals_generated_independent_verification_pending',bindings=bindings,summaries=summaries,scope='Original state unchanged. Per-class exact feasibility on reported finite domains; all-class union diagnostic only. No objective admission/native benefit.'),stream,indent=2)

if __name__=='__main__':main()
