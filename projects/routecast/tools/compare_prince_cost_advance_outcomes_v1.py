"""Paired policy-dependent outcomes and common-prefix support, failures retained."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from evaluate_prince_ready_owner_forecast_v1 import final_owners
from verify_prince_ownership_ledger_v2 import owner_payload
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_cost_advance_ablation_trial_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def pairs(owners):return {(net,n) for net,ns in owners.items() for n in ns}
def query_table(p):return {int(x[0]):tuple(map(int,x)) for x in (line.split() for line in p.open())}
def main():
 vp=D/'verification.json';v=load(vp);physical=load(D/'independent_physical_verification_v1.json');phys={r['case']:r for r in physical['rows']};hf=E/'prince_cumulative_prefix_novelty_v1_2026-10-20/frozen_inputs.json';hist={r['case']:r for r in load(hf)['rows']};hp=E/'prince_cumulative_prefix_novelty_v1_2026-10-20/verification.json';prior={r['case']:r for r in load(hp)['rows']};bindings={str(p):sha(p) for p in [vp,D/'independent_physical_verification_v1.json',D/'policy_inference_verification_v2.json',hf,hp,Path(__file__)]};rows=[];bycase={r['case']:r for r in v['rows']}
 for base in sorted({r['case'].rsplit('/',1)[0] for r in v['rows']}):
  control=bycase[base+'/native'];src=D/base/'native';gold=pairs(final_owners(src/'output.route'));qcontrol=query_table(src/'queries.tsv');ready=control['ready_iteration'];rp=set();observed=set()
  if ready is not None:
   it,owners=owner_payload(src/'owners'/f'owners_{ready}.bin');assert it==ready;rp=pairs(owners)
   for x in map(json.loads,Path(hist[base]['path']).open()):
    if x['preheap_events']:observed.add((x['net'],x['node']))
  for mode in ['native','hold_pres','hold_acc','hold_both']:
   full=base+'/'+mode;row=bycase[full];d=D/full;fp=pairs(final_owners(d/'output.route'));q=query_table(d/'queries.tsv');new=fp-rp;unseen=new-observed;frames={}
   if ready is not None:
    for offset in [1,2]:
     i=ready+offset;frames[str(offset)]=dict(search_query_summary_equal=q.get(i)==qcontrol.get(i),both_phases_exist=i in q and i in qcontrol)
    if mode=='native':assert len(new)==prior[base]['new_final_owner_pairs'] and len(unseen)==prior[base]['novelty']['preheap']['new_owner_pair_classes']['never_seen']
   oldnets={net for net,n in gold};nets={net for net,n in fp};changed_nets=sum({n for nn,n in fp if nn==net}!={n for nn,n in gold if nn==net} for net in oldnets|nets)
   result=dict(case=full,status='ACTIVATED_POLICY_OUTCOME' if ready is not None else 'UNACTIVATED_FAILURE_PRESERVED',native_exit_code=row['native_exit_code'],iterations=row['iterations'],control_iterations=control['iterations'],eligible_legal_label=phys[full]['eligible_legal_label'],terminal_overuse_units=phys[full]['overflow_units'],terminal_owner_pairs=len(fp),owner_pairs_changed_from_control=len(fp^gold),NETs_with_changed_terminal_CHANNELs=changed_nets,global_occupied_resources_changed=len({n for net,n in fp}^{n for net,n in gold}),post_ready_search_comparisons=frames)
   if ready is not None:result.update(new_terminal_owner_pairs=len(new),new_terminal_pairs_not_in_common_prefix=len(unseen),unobserved_common_prefix_fraction=len(unseen)/len(new) if new else None,target_scope='Policy-specific printed terminal owner sets;failed/overused outputs are not legal prediction labels.')
   else:assert row['iterations']==control['iterations'] and row['native_exit_code']==control['native_exit_code'] and fp==gold and not phys[full]['eligible_legal_label']
   rows.append(result);bindings[str(d/'receipt.json')]=sha(d/'receipt.json');print('COST_POLICY_OUTCOME',full,result['iterations'],result['eligible_legal_label'],result['terminal_overuse_units'],result['owner_pairs_changed_from_control'],flush=True)
 activated=[r for r in rows if r['status']=='ACTIVATED_POLICY_OUTCOME'];summary={m:dict(legal=sum(r['eligible_legal_label'] for r in activated if r['case'].endswith('/'+m)),failed=sum(not r['eligible_legal_label'] for r in activated if r['case'].endswith('/'+m))) for m in ['native','hold_pres','hold_acc','hold_both']};assert len(rows)==36 and summary==dict(native=dict(legal=6,failed=0),hold_pres=dict(legal=5,failed=1),hold_acc=dict(legal=4,failed=2),hold_both=dict(legal=0,failed=6));assert all(sha(p)==h for p,h in bindings.items())
 with (D/'outcome_comparison_v1.json').open('x') as f:json.dump(dict(status='ALL36_PAIRED_POLICY_OUTCOMES_AND_PREFIX_NOVELTY_RECORDED',rows=rows,activated_summary=summary,unactivated_failed_runs=12,bindings=bindings,scope='Causal component interventions with native stopping rules preserved. No assertion held-cost policy is mathematically infeasible. Policy-specific outputs not substitute default-native labels;no width/case selector,native predictive utility,fullpaid,unseen or hardware claim.'),f,indent=2);f.write('\n')
if __name__=='__main__':main()
