"""Diagnostic whole-NET/unique-NET ledger audit of frozen depth3 matchings."""
import json,sys
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from criticality_net_admission_v1 import validate
from versioned_digest_cache_v1 import Cache

def main():
 source=R/'experiments/mmc_three_edge_terminal_probe_v1_2026-10-18'
 proof=R/'experiments/mmc_three_edge_terminal_verification_v1_2026-10-18/verification.json'
 v=json.loads(proof.read_text());assert v['status']=='pass'
 bindings={**v['bindings'],str(proof):sha(proof),**closure([Path(__file__)])}
 protocol=json.loads((source/'protocol.json').read_text())
 out=R/'experiments/mmc_terminal_combination_audit_v1_2026-10-18';out.mkdir()
 with (out/'protocol.json').open('x') as stream:
  json.dump(dict(bindings=bindings,inputs=protocol['inputs'],selection='Exactly producer deterministic depth3 complete matchings, each feasible class separately and union of all feasible classes. No alternative or outcome-selected matching.',audit='Rebuild original all-NET unique ownership and compare full frame ledger; validate combined complete NET paths; compute replacement ownership deltas, per-type overflow, delay deltas. Invalid combined trees are reported without a valid ledger claim.',scope='Diagnostic only. Original frames unchanged, no objective/atomic admission, native run or full-flow gain.'),stream,indent=2)
 cache=Cache();summaries=[]
 with cache.installed():
  assert all(sha(p)==h for p,h in bindings.items())
  _,digest,nodes,f,rc,_=load_endpoints(protocol['inputs']['case_01']['endpoint'])
  kinds=[n.get('type') for n in nodes];caps=f['capacities']
  for case,data in protocol['inputs'].items():
   frame=json.loads(Path(data['frame']).read_text());artifact=json.loads((source/(case+'.json')).read_text())
   assert frame['graph_sha256']==digest and frame['scale']==rc.scale
   groups=defaultdict(list);records={r['connection_id']:r for r in frame['records']}
   for r in records.values():groups[r['net_id']].append(r)
   batches=[];union={}
   for c in artifact['classes']:
    arm=c['arms']['3']
    if not arm['matching']['feasible']:continue
    replacements={}
    for cid,pin in arm['matching']['matching'].items():
     cid=int(cid);r=records[cid];candidate=arm['candidates'][str(cid)][str(pin)]
     replacements[cid]=dict(r,answer=dict(status='FOUND',delay=candidate['delay'],physical_edge_ids=r['answer']['physical_edge_ids'][:-3]+candidate['tail_edges']))
    assert not union.keys()&replacements.keys();union.update(replacements)
    batches.append((str(c['sink_RR']),replacements))
   batches.append(('all_feasible_classes',union))
   needed={e for r in records.values() for e in r['answer']['physical_edge_ids']}
   needed.update(e for r in union.values() for e in r['answer']['physical_edge_ids'])
   slots={e:s for s,e in enumerate(f['edge_ids']) if e in needed};assert slots.keys()==needed
   touched={r['net_id'] for r in union.values()};old_owned={};queries={};rebuilt=Counter()
   for net,rs in groups.items():
    qs=[{k:r[k] for k in ['connection_id','net_id','source','sink']} for r in rs]
    audit=validate(f,rc,slots,qs,rs);rebuilt.update(audit['owned'])
    if net in touched:old_owned[net]=audit['owned'];queries[net]=qs
   ledger={int(p):n for p,n in frame['ledger'].items() if n}
   assert dict(rebuilt)==ledger
   def overflow(state):
    totals=Counter()
    for p,n in state.items():
     if n>caps[p]:totals[kinds[p]]+=n-caps[p]
    return dict(sorted(totals.items()))
   original_overflow=overflow(ledger);assert sum(original_overflow.values())==frame['overflow_units']
   results=[]
   for label,replacements in batches:
    nets={r['net_id'] for r in replacements.values()};delta=Counter();errors=[]
    for net in sorted(nets):
     rs=[replacements.get(r['connection_id'],r) for r in groups[net]]
     try:audit=validate(f,rc,slots,queries[net],rs)
     except ValueError as error:errors.append(dict(net_id=net,reason=str(error)));continue
     for p in old_owned[net]-audit['owned']:delta[p]-=1
     for p in audit['owned']-old_owned[net]:delta[p]+=1
    base=dict(batch=label,replaced_queries=len(replacements),changed_queries=sum(r['answer']!=records[cid]['answer'] for cid,r in replacements.items()),NETs=len(nets),tree_errors=errors)
    if errors:
     results.append(dict(base,status='INVALID_COMBINED_NET_TREE'));continue
    prospective=dict(ledger)
    for p,n in delta.items():prospective[p]=prospective.get(p,0)+n;assert prospective[p]>=0
    after=overflow(prospective)
    changes=[dict(RR=p,type=kinds[p],old_occupancy=ledger.get(p,0),new_occupancy=prospective[p],capacity=caps[p]) for p,n in sorted(delta.items()) if n]
    delays=[r['answer']['delay']-records[cid]['answer']['delay'] for cid,r in replacements.items()]
    results.append(dict(base,status='COMBINED_TREE_AND_LEDGER_VALID',old_overflow=original_overflow,new_overflow=after,total_overflow_delta=sum(after.values())-frame['overflow_units'],occupancy_changes=changes,delay_delta_sum=sum(delays),delay_increased_queries=sum(x>0 for x in delays),delay_decreased_queries=sum(x<0 for x in delays),objective_admission_pending=True))
   combined=results[-1]
   summary=dict(case=case,original_all_NET_ledger_rebuilt=True,feasible_classes=len(batches)-1,individual_valid=sum(r['status']=='COMBINED_TREE_AND_LEDGER_VALID' for r in results[:-1]),combined={k:value for k,value in combined.items() if k!='occupancy_changes'})
   with (out/(case+'.json')).open('x') as stream:json.dump(dict(summary=summary,batches=results),stream,indent=2)
   summaries.append(summary);print(json.dumps(summary),flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  bindings.update({str(p):sha(p) for p in out.glob('*.json')})
  with (out/'audit.json').open('x') as stream:json.dump(dict(status='diagnostic_complete',bindings=bindings,summaries=summaries,scope='Shared graph/RC and full-NET validator. No objective admission or frame commit; residual overflow is not native routability or prediction evidence.'),stream,indent=2)

if __name__=='__main__':main()
