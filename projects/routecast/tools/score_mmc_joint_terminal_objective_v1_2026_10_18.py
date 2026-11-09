"""Read-only exact per-NET old-owner-excluded scoring at original epoch.

Sum of per-NET deltas is a diagnostic, not a new global potential or batch
admission. Original history is zero; static spans remain separately priced.
"""
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
from criticality_objective_admission_v1 import prepare
from multiplicative_net_congestion_v1 import cost
from versioned_digest_cache_v1 import Cache

def independent_score(records,criticalities,prices,destinations):
 users=defaultdict(list);total=Fraction(0)
 for r in records:
  c=criticalities[r['connection_id']];c=Fraction(c['criticality_numerator'],c['criticality_denominator'])
  total+=c*r['answer']['delay']
  for e in r['answer']['physical_edge_ids']:users[destinations[e]].append(c)
 return total+sum((1-max(cs))*prices[p] for p,cs in users.items())

def main():
 source=R/'experiments/mmc_global_terminal_subset_v1_2026-10-18'
 proof=R/'experiments/mmc_global_terminal_subset_verification_v1_2026-10-18/verification.json'
 v=json.loads(proof.read_text());assert v['status']=='pass'
 bindings={**v['bindings'],str(proof):sha(proof),**closure([Path(__file__)])}
 protocol=json.loads((source/'protocol.json').read_text());inputs={}
 for case,data in protocol['inputs'].items():
  p=R/'experiments/mmc_old_owner_pressure_feedback_v1_2026-10-18'/case/'model/protocol.json'
  old=json.loads(p.read_text());bindings[str(p)]=sha(p)
  inputs[case]=dict(data,node_base_proof=old['structural_node_base_proof'],criticality_directory=str(Path(old['criticality_input_proof']).parent))
 out=R/'experiments/mmc_joint_terminal_objective_v1_2026-10-18';out.mkdir()
 with (out/'protocol.json').open('x') as stream:
  json.dump(dict(bindings=bindings,inputs=inputs,selection='Exactly19 previously fixed global-subset classes, no reselection.',pricing='Each NET gets its own frozen original-ledger old-owner-excluded snapshot. Original accumulated history0, pres_fac1, static destination CHAN span at scale/(20e9). Both old and candidate scored against same NET snapshot, frozen original perpin criticalities.',scope='Existing singleton prepare and independent Fraction arithmetic compared; per-NET standalone overflow acceptance reported separately. Sum of these different NET snapshots is diagnostic, not a batch potential or admission. No frame mutation.'),stream,indent=2)
 cache=Cache();summaries=[]
 with cache.installed():
  assert all(sha(p)==h for p,h in bindings.items())
  _,digest,nodes,f,rc,_=load_endpoints(inputs['case_01']['endpoint'])
  weight=rc.scale//(20*10**9)
  spans={i:max(int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow')),int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')))+1 for i,n in enumerate(nodes) if n.get('type') in {'CHANX','CHANY'}}
  for case,data in inputs.items():
   base,criticalities,b=load(data['endpoint'],data['node_base_proof'],data['criticality_directory'],len(nodes),rc.scale);bindings.update(b)
   frame=json.loads(Path(data['frame']).read_text());assert frame['history']=={} and frame['graph_sha256']==digest
   candidate=json.loads((source/(case+'.json')).read_text());updates={r['connection_id']:r for r in candidate['chosen_replacements']}
   nets={r['net_id'] for r in updates.values()};groups=defaultdict(list)
   for r in frame['records']:
    if r['net_id'] in nets:groups[r['net_id']].append(r)
   needed={e for rs in groups.values() for r in rs for e in r['answer']['physical_edge_ids']}
   needed.update(e for r in updates.values() for e in r['answer']['physical_edge_ids'])
   slots={e:s for s,e in enumerate(f['edge_ids']) if e in needed};assert slots.keys()==needed
   dest={e:f['dest_ranks'][s] for e,s in slots.items()};ledger={int(p):n for p,n in frame['ledger'].items()};rows=[];counts=Counter();total=Fraction(0)
   for net,old in sorted(groups.items()):
    new=[updates.get(r['connection_id'],r) for r in old]
    owned={r['source'] for r in old}|{dest[e] for r in old for e in r['answer']['physical_edge_ids']}
    resources={dest[e] for r in old+new for e in r['answer']['physical_edge_ids']}
    prices={p:cost(base[p],0,ledger.get(p,0)-(p in owned),f['capacities'][p],False,weight*spans.get(p,0)) for p in resources}
    assert all(prices[p]==base[p]*(1+max(0,ledger.get(p,0)-int(p in owned)-f['capacities'][p]+1))+weight*spans.get(p,0) for p in resources)
    queries=[{k:r[k] for k in ['connection_id','net_id','source','sink']} for r in old]
    admission=prepare(f,rc,slots,queries,old,new,ledger,criticalities,prices)
    before=independent_score(old,criticalities,prices,dest);after=independent_score(new,criticalities,prices,dest)
    assert before==admission['old_score'] and after==admission['candidate_score'] and after-before==admission['objective_delta']
    delta=after-before;total+=delta;sign='increased' if delta>0 else 'decreased' if delta<0 else 'unchanged';counts[sign]+=1
    counts['singleton_accepted']+=int(admission['accepted']);counts['singleton_overflow_increased']+=int(admission['prospective_overflow_delta']>0)
    rows.append(dict(net_id=net,old_epoch=frame['epochs'][str(net)],old_score=str(before),candidate_score=str(after),objective_delta=str(delta),objective_sign=sign,singleton_status=admission['status'],singleton_overflow_delta=admission['prospective_overflow_delta'],changed_queries=sum(a['answer']!=b['answer'] for a,b in zip(old,new))))
   summary=dict(case=case,NETs=len(rows),counts=dict(counts),sum_original_epoch_NET_objective_delta=str(total),sum_is_batch_potential=False)
   with (out/(case+'.json')).open('x') as stream:json.dump(dict(summary=summary,NETs=rows),stream,indent=2)
   summaries.append(summary);print(json.dumps(summary),flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  bindings.update({str(p):sha(p) for p in out.glob('*.json')})
  with (out/'receipt.json').open('x') as stream:json.dump(dict(status='original_epoch_NET_objectives_scored_independent_Fraction_arithmetic_pass',bindings=bindings,summaries=summaries,scope='No batch potential theorem, batch objective admission or frame mutation. Existing singleton acceptance is not transferred to the combined proposal.'),stream,indent=2)

if __name__=='__main__':main()
