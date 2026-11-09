"""Input-only bounded joint ownership branching, original complete-NET budgets."""
import json,time,itertools
from pathlib import Path
from types import SimpleNamespace
from collections import defaultdict,Counter
from array import array
from pre_route_endpoints import sha
from masked_raw_forward_v1 import Search
from MMC_zero_node_RC_shared_CSR_v1 import load
from binary_owner_capacity_v1 import solve
from bounded_resource_cbs_v1 import search as cbs
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_bounded_joint_CBS_v1_2026-10-21';D.mkdir(exist_ok=False);S=R/'experiments/mmc_cover_plus151_residual_v1_2026-10-21';P=S/'verification.json';v=json.loads(P.read_text());A=S/'independent_verification_v1.json';audit=json.loads(A.read_text());assert audit['all_within_budget']==453 and all(sha(p)==h for p,h in audit['bindings'].items());assert all(sha(p)==h for key in ['bindings','files'] for p,h in v[key].items());F=R/'experiments/mmc_coupled_chooser_cost_and_data_scope_v1_2026-10-19/input_only_choice_protocol_v1.json';frozen=json.loads(F.read_text());graph=next(Path(p) for p in v['bindings'] if p.endswith('.xml'));binary=R/'experiments/wide_cost_backend_build_v1_2026-10-13/search.so';bindings={str(p):sha(p) for p in [P,A,F,graph,binary,Path(__file__),R/'tools/bounded_resource_cbs_v1.py',R/'tools/masked_raw_forward_v1.py',R/'tools/wide_cost_search_bridge_v2.py',R/'tools/MMC_zero_node_RC_shared_CSR_v1.py',R/'tools/binary_owner_capacity_v1.py']};limits={'max_states':32,'max_queries':64,'max_seconds':45}
(D/'protocol.json').write_text(json.dumps({'limits_per_case':limits,'cases':['case_01','case_02','case_03'],'policy':'All37 extended NETs reroutable on original RR; fixed old keeper and unextended mandatory masks. Branch on individual positive capacity1 CHANNEL conflicts. For unextended A/B UNSAT, branch on every extended owner/resource use in the contradictory implication core; remaining A/B choices exact2SAT. Complete unchanged-budget shortest trees only; no native labels.','scope':'Bounded exploration, limits are not UNSAT, fixed domain only. No prediction, STA/native legality or end-to-end gain claim.','bindings':bindings},indent=2)+'\n')
start=time.perf_counter();row,dest,cost,caps,kinds,_=load(graph);channels={n for n,k in enumerate(kinds) if k in ['CHANX','CHANY'] and caps[n]>0};assert len(channels)==258720 and all(caps[n]==1 for n in channels);engine=Search({'row_offsets':row,'dest_ranks':dest,'capacities':caps},SimpleNamespace(increments=cost,initial=lambda n:0),binary);setup=time.perf_counter()-start;rows=[];files={};print('CBS SETUP',setup,flush=True)
try:
 for case in ['case_01','case_02','case_03']:
  case_start=time.perf_counter();work=D/case;work.mkdir();old={i['net_id']:json.loads(Path(i['result']).read_text()) for i in v['rows'] if i['case']==case};initial={};base_masks={n:set(r['blocked_nodes']) for n,r in old.items()}
  for net,r in old.items():
   support={node for q in r['connections'] for node in [q['source'],*(dest[e] for e in q['physical_edge_ids'])]}&channels
   initial[net]={'support':support,'cost':sum(q['minimum'] for q in r['connections']),'result':next(i['result'] for i in v['rows'] if i['case']==case and i['net_id']==net)}
  bp=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19'/case/'banks.jsonl';assert sha(bp)==frozen['bindings'][str(bp)];bindings[str(bp)]=sha(bp);banks={r['net_id']:(set(r['A'])&channels,set(r['B'])&channels) for r in map(json.loads,bp.open())};assert len(banks)==55300
  common=defaultdict(list);variable=defaultdict(list)
  for net,(aa,bb) in banks.items():
   if net in old:continue
   for n in aa&bb:common[n].append(net)
   for n in aa-bb:variable[n].append((net,False))
   for n in bb-aa:variable[n].append((net,True))
  assert all(len(ns)<=1 for ns in common.values());base_clauses=[];base_w=[]
  for n,lits in sorted(variable.items()):
   for clause in ([(lit,) for lit in lits] if common[n] else itertools.combinations(sorted(lits),2)):base_clauses.append(clause);base_w.append(n)
  counters={'assessments':0,'queries':0};last={}
  def assess(trees):
   counters['assessments']+=1;owners=defaultdict(list)
   for net,t in trees.items():
    for n in t['support']:owners[n].append(net)
   conflict=None;answer=None;clauses=list(base_clauses);witness=list(base_w)
   for n,ns in sorted(owners.items()):
    if len(ns)+len(common[n])>1:conflict=[(net,n) for net in sorted(ns)];break
   if conflict is None:
    for n in sorted(owners):
     for lit in variable[n]:clauses.append((lit,));witness.append(n)
    answer=solve(set(banks)-set(old),clauses)
    if answer['satisfiable']:
     picks=answer['assignment'];ledger=Counter(n for net,(aa,bb) in banks.items() for n in (trees[net]['support'] if net in old else bb if picks[net] else aa));assert all(x<=1 for x in ledger.values())
    else:
     core={step['clause'] for k in ['false_to_true','true_to_false'] for step in answer[k]};conflict=sorted({(net,witness[k]) for k in core for net in owners[witness[k]]})
   state={'assessment':counters['assessments'],'trees':{n:t['result'] for n,t in trees.items()},'conflict':conflict,'result':answer,'forbidden':clauses if answer is not None else [],'clause_channels':witness if answer is not None else []};p=work/('assessment_%03d.json'%counters['assessments']);p.write_text(json.dumps(state,indent=2)+'\n');files[str(p)]=sha(p);last.clear();last.update(state);return conflict
  def reroute(net,extra):
   counters['queries']+=1;tick=time.perf_counter();r=old[net];blocked=base_masks[net]|set(extra);qs=r['connections'];answer=engine.query(r['source'],{q['sink'] for q in qs},blocked);out=work/('query_%03d_NET_%d'%(counters['queries'],net));out.mkdir();raw=array('Q');raw.frombytes(answer['raw_u128_bytes']);assert all(raw[2*n+1]==0 for n in range(len(caps)) if answer['settled_bytes'][n]);potential=array('Q',(raw[2*n] if answer['settled_bytes'][n] else answer['cutoff'] for n in range(len(caps))));(out/'potential.u64').write_bytes(potential.tobytes());(out/'reachable.u8').write_bytes(answer['settled_bytes']);connections=[];support=set()
   for q in qs:
    a=answer['answers'][q['sink']];slots=a.get('slots',[]);passed=a['reachable'] and a['minimum']<=q['budget'];connections.append(dict(connection_id=q['connection_id'],source=q['source'],sink=q['sink'],budget=q['budget'],reachable=a['reachable'],minimum=a.get('minimum'),within_budget=passed,physical_edge_ids=slots));support.update(dest[e] for e in slots)
   good=all(q['within_budget'] for q in connections);result=dict(case=case,net_id=net,source=r['source'],initial=answer['initial'],cutoff=answer['cutoff'],blocked_nodes=sorted(blocked),extra_forbidden=sorted(extra),connections=connections,all_connections_within_budget=good,potential_file=str(out/'potential.u64'),reachable_file=str(out/'reachable.u8'),seconds=time.perf_counter()-tick);p=out/'result.json';p.write_text(json.dumps(result,indent=2)+'\n')
   for f in out.iterdir():files[str(f)]=sha(f)
   print('CBS QUERY',case,counters['queries'],net,'budget',good,flush=True)
   return {'support':support&channels,'cost':sum(q['minimum'] for q in connections),'result':str(p)} if good else None
  answer=cbs(initial,assess,reroute,lambda ts:sum(t['cost'] for t in ts.values()),**limits);answer.pop('trees',None);answer['masks']={n:sorted(mask) for n,mask in answer.get('masks',{}).items()};answer.update(case=case,last_assessment=last['assessment'],case_total_seconds=time.perf_counter()-case_start);p=work/'result.json';p.write_text(json.dumps(answer,indent=2)+'\n');files[str(p)]=sha(p);rows.append(answer);print('CBS CASE',case,answer['status'],answer['expanded'],answer['queries'],flush=True)
finally:engine.close()
assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps({'rows':rows,'setup_seconds':setup,'total_seconds':time.perf_counter()-start,'bindings':bindings,'files':files,'independent_verification_pending':True,'scope':'Only fixed keeper/cover with unextended frozen A/B library. Limit or exhaustion cannot be promoted to complete RR impossibility; all new lower-bound/primal proofs and terminal assignments require independent audit.'},indent=2)+'\n')
