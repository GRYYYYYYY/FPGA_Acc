"""Fixed all-case integer-work/QoR component gate after independent full replay."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 T=R/'experiments/mmc_native_excess_trace_replay_v1_2026-10-19';vp=T/'verification.json'
 if not vp.exists():raise SystemExit('NOT_READY: all6 independently replayed traces required')
 v=json.loads(vp.read_text());assert v['status']=='all6_excess_utility_native_traces_independently_replayed' and len(v['runs'])==6
 for p,h in v['bindings'].items():assert sha(p)==h,p
 P=R/'experiments/mmc_native_excess_utility_protocol_v1_2026-10-19/protocol.json';N=R/'experiments/mmc_native_excess_utility_v1_2026-10-19';O=R/'experiments/mmc_native_excess_utility_review_v1_2026-10-19';O.mkdir();keys=['NET_operations','connection_operations','heap_pushes','heap_pops'];rows=[];bindings={str(vp):sha(vp),str(P):sha(P),str(pathlib.Path(__file__).resolve()):sha(__file__)}
 for case in [f'episode_{i:02d}' for i in range(1,4)]:
  arms={}
  for arm in ['zero','forecast']:
   tp=T/(case+'_'+arm+'.json');assert v['bindings'][str(tp)]==sha(tp);trace=json.loads(tp.read_text());p=N/case/arm/'verification.json';a=json.loads(p.read_text());assert trace['bindings'][str(p)]==sha(p) and a['all_native_physical_and_canonical_pass'];native=a['rows'][0];assert native['policy_arm']==arm;assert native['preload_state']['all_nodes_checked']==904438 and native['preload_state']['all_bits_match_fixed_one_pseudo_iteration']
   if arm=='zero':assert native['zero_matches_archived_same_case_full_bytes_and_work']
   total={k:sum(row[k] for row in trace['iteration_stats']) for k in keys};arms[arm]=dict(work=total,iterations=len(trace['iteration_stats']),wirelength=native['wirelength'],diagnostic_cpd_ns=native['diagnostic_cpd_ns'],initial_costs=native['preload_state'],canonical_fixups=native['canonical']['fixups'],original_zero_counter_gate_pass=native['canonical']['original_zero_counter_gate_pass'],native_process_seconds_diagnostic_only=native['native_process_seconds']);bindings[str(tp)]=sha(tp);bindings[str(p)]=sha(p)
  zero,on=arms['zero'],arms['forecast'];nonreg={k:on['work'][k]<=zero['work'][k] for k in keys};strict={k:on['work'][k]<zero['work'][k] for k in keys};wire_ok=on['wirelength']<=zero['wirelength'];cpd_ok=on['diagnostic_cpd_ns']<=zero['diagnostic_cpd_ns']+1e-12;passed=all(nonreg.values()) and any(strict.values()) and wire_ok and cpd_ok;rows.append(dict(case=case,arms=arms,work_nonregression=nonreg,work_strict_improvement=strict,wire_nonregression=wire_ok,diagnostic_cpd_nonregression=cpd_ok,primary_native_component_gate_pass=passed));print('NATIVE UTILITY GATE',case,passed,flush=True)
 allpass=all(x['primary_native_component_gate_pass'] for x in rows)
 result=dict(status='ALL6_NATIVE_COMPONENT_UTILITY_COMPARISONS_COMPLETE',bindings=bindings,cases=rows,all3_primary_native_component_gate_pass=allpass,candidate_promoted=False,original_final_occupancy_gate_pass=False,strict_unseen_family_admitted=False,complete_workflow_gain_proven=False,hardware_gain_proven=False,scope='Fixed initial PathFinder cost preload component experiment on exposed MMC layouts. All4 measured integer work counters and wire/diagnostic CPD gates required for every case. Physical/canonical semantic and actual initialized-cost readback passed. Original canonical zero-counter and final-occupancy gates remain separate failures. Instrumented native process clocks are diagnostic, predictor/import/export/replay/verification costs are not excluded from future fullworkflow accounting.')
 with (O/'comparison.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 decision={**result,'status':'NATIVE_COMPONENT_GATE_PASSED_NOT_PROMOTED' if allpass else 'NATIVE_COMPONENT_GATE_FAILED_NOT_PROMOTED'}
 with (O/'research_decision_v1.json').open('x') as f:json.dump(decision,f,indent=2);f.write('\n')
if __name__=='__main__':main()
