"""Objective-constrained fixed-subset diagnostic and full repricing delta."""
import json,sys
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from load_design_routing_inputs_v2 import load
from criticality_net_admission_v1 import validate
from criticality_objective_admission_v1 import score
from score_mmc_joint_terminal_objective_v1_2026_10_18 import independent_score
from multiplicative_net_congestion_v1 import cost
from versioned_digest_cache_v1 import Cache

def main():
 prior=R/'experiments/mmc_global_terminal_subset_v1_2026-10-18'
 proof=R/'experiments/mmc_global_terminal_subset_verification_v1_2026-10-18/verification.json'
 scoring=R/'experiments/mmc_joint_terminal_objective_v1_2026-10-18'
 v=json.loads(proof.read_text());sv=json.loads((scoring/'receipt.json').read_text());assert v['status']=='pass'
 bindings={**v['bindings'],**sv['bindings'],str(proof):sha(proof),str(scoring/'receipt.json'):sha(scoring/'receipt.json'),**closure([Path(__file__)])}
 inputs=json.loads((scoring/'protocol.json').read_text())['inputs']
 out=R/'experiments/mmc_objective_terminal_subset_v1_2026-10-18';out.mkdir()
 with (out/'protocol.json').open('x') as stream:
  json.dump(dict(bindings=bindings,inputs=inputs,selection='Same20 fixed class proposals and all2180 apply/retain subsets. Require each affected NET same-original-snapshot objective delta<=0 in addition to all previous resource/tree constraints.',ranking='Unchanged diagnostic ranking: maximize applied classes, then minimize overflow, changed queries and SINK tuple.',global_check='For chosen subset, compute exact full before/after self-consistently repriced objective delta, including unchanged external NETs touching changed node prices. This global check is distinct from existing singleton frozen-snapshot scoring.',scope='Read-only diagnostic, no atomic admitted frame or changed native policy. Fixed candidate domains only; no complete-route feasibility or runtime gain.'),stream,indent=2)
 cache=Cache();summaries=[]
 with cache.installed():
  assert all(sha(p)==h for p,h in bindings.items())
  _,digest,nodes,f,rc,_=load_endpoints(inputs['case_01']['endpoint']);caps=f['capacities'];weight=rc.scale//(20*10**9)
  spans={i:max(int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow')),int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')))+1 for i,n in enumerate(nodes) if n.get('type') in {'CHANX','CHANY'}}
  for case,data in inputs.items():
   base,criticalities,b=load(data['endpoint'],data['node_base_proof'],data['criticality_directory'],len(nodes),rc.scale);bindings.update(b)
   frame=json.loads(Path(data['frame']).read_text());assert frame['history']=={} and frame['graph_sha256']==digest
   previous=json.loads((prior/(case+'.json')).read_text())
   proposals=json.loads((R/'experiments/mmc_resource_constrained_terminal_v1_2026-10-18'/(case+'.json')).read_text())
   classes=sorted((c for c in proposals['classes'] if c['resource_assignment']['feasible']),key=lambda c:c['sink_RR'])
   assert [c['sink_RR'] for c in classes]==previous['class_order']
   replacements={i:{r['connection_id']:r for r in c['replacements']} for i,c in enumerate(classes)}
   groups=defaultdict(list)
   for r in frame['records']:groups[r['net_id']].append(r)
   records={r['connection_id']:r for r in frame['records']};net_classes=defaultdict(set)
   for i,rows in replacements.items():
    for r in rows.values():net_classes[r['net_id']].add(i)
   needed={e for r in frame['records'] for e in r['answer']['physical_edge_ids']}
   needed.update(e for rows in replacements.values() for r in rows.values() for e in r['answer']['physical_edge_ids'])
   slots={e:s for s,e in enumerate(f['edge_ids']) if e in needed};assert slots.keys()==needed
   dest={e:f['dest_ranks'][s] for e,s in slots.items()};ledger={int(p):n for p,n in frame['ledger'].items()}
   patterns={};pattern_rows=[]
   for p in previous['NET_patterns']:
    net=p['net_id'];mask=p['mask']
    if not p['valid']:continue
    old=groups[net];updates={cid:r for i in net_classes[net] if mask>>i&1 for cid,r in replacements[i].items() if r['net_id']==net}
    new=[updates.get(r['connection_id'],r) for r in old]
    qs=[{k:r[k] for k in ['connection_id','net_id','source','sink']} for r in old]
    oa=validate(f,rc,slots,qs,old);na=validate(f,rc,slots,qs,new)
    resources={dest[e] for r in old+new for e in r['answer']['physical_edge_ids']}
    prices={p:cost(base[p],0,ledger.get(p,0)-(p in oa['owned']),caps[p],False,weight*spans.get(p,0)) for p in resources}
    before=score(f,slots,old,criticalities,prices,oa['delays']);after=score(f,slots,new,criticalities,prices,na['delays'])
    assert before==independent_score(old,criticalities,prices,dest) and after==independent_score(new,criticalities,prices,dest)
    delta=after-before;patterns[(net,mask)]=delta
    pattern_rows.append(dict(net_id=net,mask=mask,objective_delta=str(delta)))
   rows=[];best=None;chosen=None
   for row in previous['subsets']:
    mask=row['mask'];violations=[]
    for net,indices in net_classes.items():
     local=mask&sum(1<<i for i in indices)
     if (net,local) in patterns and patterns[(net,local)]>0:violations.append(net)
    valid=row['valid'] and not violations
    selected=[i for i in range(len(classes)) if mask>>i&1]
    key=(-len(selected),row['total_overflow'],row['changed_queries'],tuple(classes[i]['sink_RR'] for i in selected))
    rows.append(dict(mask=mask,resource_valid=row['valid'],objective_increased_NETs=sorted(violations),valid=valid))
    if valid and (best is None or key<best):best=key;chosen=mask
   assert chosen is not None
   updates={cid:r for i in range(len(classes)) if chosen>>i&1 for cid,r in replacements[i].items()}
   delta=Counter()
   for p in previous['NET_patterns']:
    net=p['net_id'];local=chosen&sum(1<<i for i in net_classes[net])
    if p['mask']==local:assert p['valid'];delta.update(p['added']);delta.subtract(p['removed'])
   after_ledger=dict(ledger)
   for p,n in delta.items():after_ledger[p]=after_ledger.get(p,0)+n;assert after_ledger[p]>=0
   def owner_price(p,counts):return base[p]*(1+max(0,counts.get(p,0)-caps[p]))+weight*spans.get(p,0)
   repriced={p for p,n in delta.items() if n and owner_price(p,ledger)!=owner_price(p,after_ledger)}
   changed_nets={r['net_id'] for cid,r in updates.items() if r['answer']!=records[cid]['answer']}
   global_delta=Fraction(0);external_delta=Fraction(0);scored_nets=0
   for net,old in groups.items():
    if net not in changed_nets and not any(dest[e] in repriced for r in old for e in r['answer']['physical_edge_ids']):continue
    new=[updates.get(r['connection_id'],r) for r in old]
    resources={dest[e] for r in old+new for e in r['answer']['physical_edge_ids']}
    old_prices={p:owner_price(p,ledger) for p in resources};new_prices={p:owner_price(p,after_ledger) for p in resources}
    change=independent_score(new,criticalities,new_prices,dest)-independent_score(old,criticalities,old_prices,dest)
    global_delta+=change;scored_nets+=1
    if net not in changed_nets:external_delta+=change;assert change<=0
   assert global_delta<=0
   summary=dict(case=case,subsets_examined=len(rows),valid_subsets=sum(r['valid'] for r in rows),selected_classes=-best[0],chosen_mask=chosen,original_overflow=frame['overflow_units'],proposal_overflow=best[1],changed_queries=best[2],self_consistent_global_objective_delta=str(global_delta),unchanged_external_NET_objective_delta=str(external_delta),repriced_nodes=len(repriced),global_delta_NETs_scored=scored_nets)
   with (out/(case+'.json')).open('x') as stream:json.dump(dict(summary=summary,NET_pattern_objectives=pattern_rows,subsets=rows,chosen_replacements=list(updates.values()),objective_admission_contract_not_yet_committed=True),stream,indent=2)
   summaries.append(summary);print(json.dumps(summary),flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  bindings.update({str(p):sha(p) for p in out.glob('*.json')})
  with (out/'receipt.json').open('x') as stream:json.dump(dict(status='objective_constrained_subset_and_full_repricing_diagnostic_complete',bindings=bindings,summaries=summaries,scope='No original frame mutation, epoch transaction or native run. Independent arithmetic shares input decoding; subset objective ranking and full repricing still require independent audit.'),stream,indent=2)

if __name__=='__main__':main()
