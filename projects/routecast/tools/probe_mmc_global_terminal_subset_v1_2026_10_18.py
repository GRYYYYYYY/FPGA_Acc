"""Exact apply/retain subset search over fixed resource-feasible class proposals.

This does not optimize alternative within-class matchings or certify the
existing criticality objective; output remains a diagnostic proposal.
"""
import json,sys,itertools
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
 source=R/'experiments/mmc_resource_constrained_terminal_v1_2026-10-18'
 proof=R/'experiments/mmc_resource_terminal_verification_v1_2026-10-18/verification.json'
 prior=R/'experiments/mmc_terminal_combination_audit_v1_2026-10-18/audit.json'
 v=json.loads(proof.read_text());a=json.loads(prior.read_text());assert v['status']=='pass' and a['status']=='diagnostic_complete'
 bindings={**v['bindings'],**a['bindings'],str(proof):sha(proof),str(prior):sha(prior),**closure([Path(__file__)])}
 protocol=json.loads((source/'protocol.json').read_text())
 out=R/'experiments/mmc_global_terminal_subset_v1_2026-10-18';out.mkdir()
 with (out/'protocol.json').open('x') as stream:
  json.dump(dict(bindings=bindings,inputs=protocol['inputs'],selection='Every fixed resource-feasible class proposal from the previous producer. Exhaust every apply/retain subset, including retaining all original paths.',constraints='Full combined NET trees and original RC budgets; no node overflow increases; applied-class IPIN pools must be within capacity.',ranking='Maximize applied classes, then minimize total overflow, then changed queries, then ascending tuple of selected SINK IDs. This is a diagnostic subset criterion, not the existing criticality objective.',scope='No alternate within-class matching optimization, model commit, criticality objective admission or native gain.'),stream,indent=2)
 cache=Cache();summaries=[]
 with cache.installed():
  assert all(sha(p)==h for p,h in bindings.items())
  _,digest,nodes,f,rc,_=load_endpoints(protocol['inputs']['case_01']['endpoint'])
  caps=f['capacities'];kinds=[n.get('type') for n in nodes]
  for case,data in protocol['inputs'].items():
   frame=json.loads(Path(data['frame']).read_text());assert frame['graph_sha256']==digest
   produced=json.loads((source/(case+'.json')).read_text())
   initial=json.loads((R/'experiments/mmc_terminal_assignment_probe_v1_2026-10-18'/(case+'.json')).read_text())
   pools={c['sink_RR']:set(map(int,c['available_IPIN_capacity'])) for c in initial['classes']}
   classes=sorted((c for c in produced['classes'] if c['resource_assignment']['feasible']),key=lambda c:c['sink_RR'])
   records={r['connection_id']:r for r in frame['records']};ledger={int(p):n for p,n in frame['ledger'].items()}
   replacements={};net_classes=defaultdict(set)
   for i,c in enumerate(classes):
    replacements[i]={r['connection_id']:r for r in c['replacements']}
    for r in c['replacements']:net_classes[r['net_id']].add(i)
   groups=defaultdict(list)
   for r in records.values():
    if r['net_id'] in net_classes:groups[r['net_id']].append(r)
   needed={e for rs in groups.values() for r in rs for e in r['answer']['physical_edge_ids']}
   needed.update(e for rows in replacements.values() for r in rows.values() for e in r['answer']['physical_edge_ids'])
   slots={e:s for s,e in enumerate(f['edge_ids']) if e in needed};assert slots.keys()==needed
   queries={net:[{k:r[k] for k in ['connection_id','net_id','source','sink']} for r in rs] for net,rs in groups.items()}
   old_owned={net:validate(f,rc,slots,queries[net],rs)['owned'] for net,rs in groups.items()}
   tables={};patterns=[]
   for net,indices in sorted(net_classes.items()):
    ids=sorted(indices);tables[net]={}
    for bits in itertools.product([False,True],repeat=len(ids)):
     mask=sum(1<<i for i,b in zip(ids,bits) if b)
     updates={cid:r for i,b in zip(ids,bits) if b for cid,r in replacements[i].items() if r['net_id']==net}
     rs=[updates.get(r['connection_id'],r) for r in groups[net]]
     try:owned=validate(f,rc,slots,queries[net],rs)['owned']
     except ValueError as error:
      row=dict(net_id=net,mask=mask,valid=False,error=str(error))
     else:
      row=dict(net_id=net,mask=mask,valid=True,added=sorted(owned-old_owned[net]),removed=sorted(old_owned[net]-owned))
     patterns.append(row);tables[net][mask]=row
   original_overflow=sum(max(0,n-caps[p]) for p,n in ledger.items());assert original_overflow==frame['overflow_units']
   rows=[];best=None;best_mask=None
   for mask in range(1<<len(classes)):
    selected=[i for i in range(len(classes)) if mask>>i&1];change=Counter();invalid=[]
    for net,indices in net_classes.items():
     local=mask&sum(1<<i for i in indices);pattern=tables[net][local]
     if not pattern['valid']:invalid.append(net);continue
     change.update(pattern['added']);change.subtract(pattern['removed'])
    growth=sorted(p for p,n in change.items() if ledger.get(p,0)+n>max(ledger.get(p,0),caps[p]))
    unrepaired=sorted(p for i in selected for p in pools[classes[i]['sink_RR']] if ledger.get(p,0)+change[p]>caps[p])
    total=original_overflow+sum(max(0,ledger.get(p,0)+n-caps[p])-max(0,ledger.get(p,0)-caps[p]) for p,n in change.items())
    updates={cid:r for i in selected for cid,r in replacements[i].items()}
    changed=sum(r['answer']!=records[cid]['answer'] for cid,r in updates.items())
    valid=not invalid and not growth and not unrepaired
    row=dict(mask=mask,applied_classes=len(selected),valid=valid,invalid_NETs=invalid,overflow_growth_nodes=growth,unrepaired_selected_IPINs=unrepaired,total_overflow=total,changed_queries=changed)
    rows.append(row)
    key=(-len(selected),total,changed,tuple(classes[i]['sink_RR'] for i in selected))
    if valid and (best is None or key<best):best=key;best_mask=mask
   assert best_mask is not None and rows[0]['valid']
   selected=[i for i in range(len(classes)) if best_mask>>i&1]
   updates={cid:r for i in selected for cid,r in replacements[i].items()};delta=Counter()
   for net,indices in net_classes.items():
    pattern=tables[net][best_mask&sum(1<<i for i in indices)];assert pattern['valid']
    delta.update(pattern['added']);delta.subtract(pattern['removed'])
   bytype=Counter()
   for p in ledger.keys()|delta.keys():bytype[kinds[p]]+=max(0,ledger.get(p,0)+delta[p]-caps[p])
   summary=dict(case=case,available_classes=len(classes),subsets_examined=len(rows),valid_subsets=sum(r['valid'] for r in rows),chosen_mask=best_mask,chosen_SINK_classes=[classes[i]['sink_RR'] for i in selected],original_overflow=original_overflow,new_overflow=sum(bytype.values()),new_overflow_by_type=dict(bytype),changed_queries=rows[best_mask]['changed_queries'],all_class_union_valid=rows[-1]['valid'])
   with (out/(case+'.json')).open('x') as stream:json.dump(dict(summary=summary,class_order=[c['sink_RR'] for c in classes],subsets=rows,NET_patterns=patterns,chosen_replacements=list(updates.values()),occupancy_changes={p:n for p,n in delta.items() if n},objective_admission_pending=True),stream,indent=2)
   summaries.append(summary);print(json.dumps(summary),flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  bindings.update({str(p):sha(p) for p in out.glob('*.json')})
  with (out/'receipt.json').open('x') as stream:json.dump(dict(status='joint_subset_proposals_generated_independent_verification_pending',bindings=bindings,summaries=summaries,scope='Exhaustive apply/retain search over fixed prior proposals only; all input frames unchanged; original criticality objective not evaluated, no native or forecast gain claim.'),stream,indent=2)

if __name__=='__main__':main()
