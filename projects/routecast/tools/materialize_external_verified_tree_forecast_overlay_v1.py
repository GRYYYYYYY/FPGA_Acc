"""Freeze one all3 complete forecast overlay before reopening exposed development labels."""
import json,sys,copy
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from zero_rc_budget_certificate_graph_v1 import load_graph
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'prospective_external_family_supplementary_development_v1_2026-10-19';T=E/'prospective_external_family_reservation_frontier_transaction_v1_2026-10-19';H=E/'prospective_external_family_joint_cut_owner_replacement_v1_2026-10-19';O=E/'prospective_external_family_verified_tree_forecast_overlay_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 O.mkdir(exist_ok=False);bindings=closure([Path(__file__)]);cases=[]
 for i in (1,2,3):
  case=f'w160/episode_{i:02d}';sp=P/'specifications'/case/'comparison_spec.json';spec=read(sp);base=Path(spec['predictions']['native_retained_on']['frame']);bp=Path(spec['predictions']['native_retained_on']['proof']);origin=H if i==2 else T;state=origin/case/'final_conditional_trees.jsonl';proof=origin/'independent_verification_v1.json';audit=read(proof);assert all(sha(p)==h for p,h in audit['bindings'].items());assert audit['bindings'][str(state)]==sha(state);bproof=read(bp);assert all(sha(p)==h for p,h in bproof['bindings'].items());assert bproof['bindings'][str(base)]==sha(base);assert bproof['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];cases.append(dict(case=case,base_frame=str(base),base_audit=str(bp),partial_state=str(state),partial_audit=str(proof),original_comparison_spec=str(sp),endpoint=spec['endpoint']))
  for p in [sp,base,bp,state,proof,Path(spec['endpoint'])]:bindings[str(p)]=sha(p)
 policy='One fixed all3 development overlay: start from original native_retained_on complete forecast; replace entire NET trees from latest independently verified private states, using frontier transaction final states for cases1/3 and older joint-owner final state for deferred case2. Keep every other NET unchanged, all original CIDs/endpoints/floors/budgets, rebuild full unique-NET and independent-connection ledgers. Increment changed NET epochs only, clear history because no feedback continuation is claimed. Global forecast overload is allowed and reported, NOT routing legality. No labels read during construction; no candidate/threshold search. Require independent full-frame physical/budget/ledger audit before original fixed forecast metrics. Existing development labels already exposed; no strict-unseen, native utility or matched full-time claim. Preserve six source-unavailable width96/128 cases in full9 availability failure.'
 pp=O/'protocol.json';pp.write_text(json.dumps(dict(policy=policy,cases=cases,bindings=bindings,unavailable_cases=[f'w{w:03d}/episode_{i:02d}' for w in (96,128) for i in (1,2,3)]),indent=2)+'\n');bindings[str(pp)]=sha(pp);graph=Path(read(cases[0]['endpoint'])['inputs']['graph']['path']);g=load_graph(graph);bindings[str(graph)]=sha(graph);rows=[]
 for spec in cases:
  base=read(spec['base_frame']);ep=read(spec['endpoint']);assert base['graph_sha256']==sha(graph)==ep['graph_sha256'];records={r['connection_id']:r for r in base['records']};assert len(records)==len(ep['connections']);groups=defaultdict(set)
  for r in records.values():groups[r['net_id']].add(r['connection_id'])
  state_rows=list(map(json.loads,Path(spec['partial_state']).read_text().splitlines()));state={r['net_id']:r['candidate'] for r in state_rows};assert len(state)==len(state_rows);changed=[];replacement_CIDs=0
  for net,candidate in state.items():
   incoming={r['connection_id']:r for r in candidate['records']};assert len(incoming)==len(candidate['records']) and set(incoming)==groups[net];different=False
   for cid,new in incoming.items():
    old=records[cid];assert {k:v for k,v in old.items() if k!='answer'}=={k:v for k,v in new.items() if k!='answer'}
    different|=old['answer']!=new['answer'];records[cid]=copy.deepcopy(new);replacement_CIDs+=1
   if different:changed.append(net)
  unions=defaultdict(set);independent=Counter()
  for r in records.values():
   ns={r['source']};ns.update(g['vs'][eid] for eid in r['answer']['physical_edge_ids']);unions[r['net_id']].update(ns);independent.update(ns)
  ledger=Counter(n for ns in unions.values() for n in ns);overflow=sum(max(0,count-g['caps'][n]) for n,count in ledger.items());epochs=dict(base['epochs'])
  for net in changed:epochs[str(net)]+=1
  out=O/spec['case'];out.mkdir(parents=True);frame=dict(records=[records[cid] for cid in sorted(records)],scale=base['scale'],graph_sha256=base['graph_sha256'],required_connections=base['required_connections'],completed_connections=len(records),ledger=dict(sorted(ledger.items())),independent_connection_ledger=dict(sorted(independent.items())),history={},epochs=epochs,overflow_units=overflow,overflow_nodes=sum(v>g['caps'][n] for n,v in ledger.items()),eligible_for_legal_route_commit=False,budget_policy=base['budget_policy'],initializer_policy='FIXED_VERIFIED_TREE_DEVELOPMENT_OVERLAY_NO_FEEDBACK_CONTINUATION',status='COMPLETE_DEVELOPMENT_FORECAST_OVERLAY_PENDING_INDEPENDENT_AUDIT');fp=out/'frame.json';fp.write_text(json.dumps(frame,separators=(',',':'))+'\n');bindings[str(fp)]=sha(fp);row=dict(case=spec['case'],overlay_NETs=len(state),changed_NETs=sorted(changed),replaced_CIDs=replacement_CIDs,all_CIDs=len(records),overflow_units=overflow,base_overflow_units=base['overflow_units'],frame=str(fp));rows.append(row);print('COMPLETE_FORECAST_OVERLAY',json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(O/'verification.json').write_text(json.dumps(dict(status='ALL3_COMPLETE_DEVELOPMENT_FORECAST_OVERLAYS_PREPARED_PENDING_INDEPENDENT_AUDIT',rows=rows,bindings=bindings,labels_opened=False,native_commits=0,scope=policy),indent=2)+'\n')
if __name__=='__main__':main()
