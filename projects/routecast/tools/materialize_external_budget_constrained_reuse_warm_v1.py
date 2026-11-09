"""Fixed old-channel-reuse endpoint repair with audited warm whole-NET fallback."""
import json,sys,copy
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from compiled_criticality_tree_v1 import Graph,BINARY
from budget_constrained_native_reuse_initializer_v1 import initialize
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'prospective_external_family_supplementary_development_v1_2026-10-19';O=E/'prospective_external_family_budget_constrained_reuse_warm_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 O.mkdir(exist_ok=False);bindings=closure([Path(__file__)]);contract=E/'budget_constrained_native_reuse_contract_v1_2026-10-19/verification.json';c=read(contract);assert c['random_graphs']==150 and c['unconstrained_overbudget_fixture_solved_within_budget_without_fallback'] and all(sha(p)==h for p,h in c['bindings'].items());bindings[str(contract)]=sha(contract);bindings[str(BINARY)]=sha(BINARY);cases=[]
 fallback_contract=E/'budget_constrained_native_reuse_fallback_contract_v1_2026-10-19/verification.json';fc=read(fallback_contract);assert fc['invalid_warm_fallback_rejected'] and all(sha(p)==h for p,h in fc['bindings'].items());bindings[str(fallback_contract)]=sha(fallback_contract)
 for i in (1,2,3):
  case=f'w160/episode_{i:02d}';sp=P/'specifications'/case/'comparison_spec.json';s=read(sp);warm=Path(s['predictions']['native_retained_on']['frame']).parent/'initial.json';wp=P/'predictions'/case/'warm/native_retained/verification.json';w=read(wp);assert w['native_staged_state_independent_xml_pass'] and all(sha(p)==h for p,h in w['bindings'].items());source=Path(s['source_frame']);ap=Path(s['source_proof']);a=read(ap);assert a['status']=='SOURCE_XML_FRACTION_PATH_BUDGET_LEDGER_AUDIT_PASS' and all(sha(p)==h for p,h in a['bindings'].items());assert a['bindings'][str(source)]==sha(source);out=O/case;cases.append(dict(case=case,endpoint=s['endpoint'],base_frame=str(warm),source_frame=str(source),warm_proof=str(wp),source_proof=str(ap),dirty_NETs=w['dirty_nets'],partial_state=str(out/'replacement_trees.jsonl'),original_comparison_spec=str(sp)))
  for p in [sp,warm,wp,source,ap,Path(s['endpoint'])]:bindings[str(p)]=sha(p)
 policy='One fixed budget-constrained native-channel-reuse initializer for ALL3 exposed cases, same original source and audited warm fallback. Current per-CID raw budget enforced INSIDE Pareto label search, lex cost=new-to-native CHANNEL additions then raw delay with same envelope+1 penalty. Fixed10000 created labels per expansion, no deadline/quota/penalty sweep. LABEL_LIMIT is UNKNOWN and forces complete audited warm NET fallback, not infeasibility. Frozen tree, native unchanged endpoint paths preserved. No global wholeNET optimality, native legal commit or full-time claim. Future fixed2x2 comparison: prior weighted-then-budget-gated reuse vs this constrained reuse, each raw-demand and bounded-utilization heads, all3 cases with original controls and four gates. All six unavailable cases retained.'
 pp=O/'protocol.json';pp.write_text(json.dumps(dict(policy=policy,cases=cases,score_plan={'initializers':['old_weighted_reuse_warm','budget_constrained_reuse_warm'],'score_heads':['raw_demand','capacity_bounded_utilization'],'all_cases_required':True},bindings=bindings,unavailable_cases=[f'w{w:03d}/episode_{i:02d}' for w in (96,128) for i in (1,2,3)]),indent=2)+'\n');bindings[str(pp)]=sha(pp);_,digest,nodes,fields,rc,_=load_endpoints(cases[0]['endpoint']);kinds=tuple(n.get('type') for n in nodes);slots={e:i for i,e in enumerate(fields['edge_ids'])};g=Graph(fields,rc.increments,[rc.initial(i) for i in range(len(nodes))]);rows=[]
 try:
  for spec in cases:
   warm=read(spec['base_frame']);source=read(spec['source_frame']);ep=read(spec['endpoint']);assert warm['graph_sha256']==source['graph_sha256']==ep['graph_sha256']==digest;old={r['connection_id']:r for r in source['records']};records={r['connection_id']:copy.deepcopy(r) for r in warm['records']};assert set(old)==set(records)=={q['connection_id'] for q in ep['connections']};groups=defaultdict(list)
   for r in warm['records']:groups[r['net_id']].append(r)
   out=O/spec['case'];out.mkdir(parents=True);events=[];changed=[]
   with Path(spec['partial_state']).open('x') as trees:
    for net in sorted(spec['dirty_NETs']):
     qs=sorted(groups[net],key=lambda r:r['connection_id']);budgets={r['connection_id']:r['budget_integer'] for r in qs};fallback={r['connection_id']:copy.deepcopy(r['answer']) for r in qs};result=initialize(g,fields,kinds,qs,[old[r['connection_id']] for r in qs],budgets,slots,lambda f=fallback:copy.deepcopy(f));new=[dict(r,answer=result['answers'][r['connection_id']]) for r in qs];changed_CIDs=[r['connection_id'] for r in new if r['answer']!=records[r['connection_id']]['answer']]
     if changed_CIDs:changed.append(net)
     for r in new:records[r['connection_id']]=r
     trees.write(json.dumps(dict(net_id=net,candidate=dict(records=new)),separators=(',',':'))+'\n');trees.flush();events.append(dict(net_id=net,changed_CIDs=changed_CIDs,**{k:v for k,v in result.items() if k not in ['answers','owner_nodes']}))
   unions=defaultdict(set);independent=Counter()
   for r in records.values():
    ns={r['source']};ns.update(fields['dest_ranks'][slots[e]] for e in r['answer']['physical_edge_ids']);unions[r['net_id']].update(ns);independent.update(ns)
   ledger=Counter(n for ns in unions.values() for n in ns);epochs=dict(warm['epochs'])
   for net in changed:epochs[str(net)]+=1
   f=dict(warm,records=[records[cid] for cid in sorted(records)],ledger=dict(ledger),independent_connection_ledger=dict(independent),epochs=epochs,overflow_units=sum(max(0,v-fields['capacities'][n]) for n,v in ledger.items()),overflow_nodes=sum(v>fields['capacities'][n] for n,v in ledger.items()),initializer_policy='BUDGET_CONSTRAINED_NATIVE_CHANNEL_REUSE_WARM_V1',status='COMPLETE_REUSE_WARM_PENDING_INDEPENDENT_AUDIT');fp=out/'frame.json';fp.write_text(json.dumps(f,separators=(',',':'))+'\n');ev=out/'events.json';ev.write_text(json.dumps(events,indent=2)+'\n');row=dict(case=spec['case'],dirty_NETs=len(spec['dirty_NETs']),changed_NETs=changed,changed_CIDs=sum(len(e['changed_CIDs']) for e in events),fallback_NETs=[e['net_id'] for e in events if e['whole_NET_fallback']],frame=str(fp),overflow=f['overflow_units']);row['search_statuses']=dict(Counter(q['status'] for e in events for q in e['repair_searches']));row['labels_created']=sum(q['labels_created'] for e in events for q in e['repair_searches']);rows.append(row)
   for p in [fp,ev,Path(spec['partial_state'])]:bindings[str(p)]=sha(p)
   print('BUDGET_CONSTRAINED_REUSE_WARM',json.dumps(row),flush=True)
 finally:g.close()
 assert all(sha(p)==h for p,h in bindings.items());(O/'verification.json').write_text(json.dumps(dict(status='ALL3_BUDGET_CONSTRAINED_REUSE_WARM_FRAMES_PREPARED_PENDING_INDEPENDENT_AUDIT',rows=rows,bindings=bindings,scope=policy),indent=2)+'\n')
if __name__=='__main__':main()
