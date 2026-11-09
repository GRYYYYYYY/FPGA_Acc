"""Consolidate all three audited actual-layout cases without filtering QoR failures."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 M=R/'experiments/mmc_reference_budget_incremental_astar_v2_2026-10-19';O=R/'experiments/mmc_reference_incremental_astar_cohort_closure_v1_2026-10-19';O.mkdir(exist_ok=False);rows=[];bindings={}
 for case in ['episode_01','episode_02','episode_03']:
  C=R/'experiments/mmc_reference_incremental_astar_canonical_v3_2026-10-19'/case
  tp=C/('independent_model_trace_verification_v1.json' if case=='episode_01' else 'independent_model_trace_verification_v2.json');sp=R/'experiments/mmc_indexed_serialization_equivalence_v1_2026-10-19'/case/'independent_equivalence_v1.json';cp=C/'receipt.json';mp=M/case/'receipt.json';docs=[json.loads(p.read_text()) for p in [tp,sp,cp]];t,s,c=docs
  for doc in docs:
   for p,h in doc['bindings'].items():assert sha(p)==h
  for p,h in c['files'].items():assert sha(p)==h
  assert c['status']=='NATIVE_CANONICAL_SEMANTIC_FULL_STA_PHYSICAL_GATE_PASS' and c['all_remaining_mismatches_native_ignored_sinks'] and c['all115572_connections_55300_NETs_physical_pass'];assert t['connections']==s['bound_sinks']==115572 and t['routed_NETs']==55300
  model=json.loads(mp.read_text());assert model['pending']==0 and model['final_present_NET_unique_CHAN_span']==t['candidate_wirelength']==c['wirelength'];wire_nonreg=t['candidate_wirelength']<=t['cold_wirelength'];cpd_nonreg=t['candidate_CPD_ns']<=t['cold_CPD_ns']+1e-12;assert t['native_wire_and_CPD_nonregression']==(wire_nonreg and cpd_nonreg)
  rows.append(dict(case=case,connections=115572,retained=t['retained_connections'],rebuilt=t['rebuilt_connections'],capacity_overflow=0,native_FULL_canonical_and_model_trace_pass=True,cold_wirelength=t['cold_wirelength'],candidate_wirelength=t['candidate_wirelength'],wirelength_delta=t['candidate_wirelength']-t['cold_wirelength'],wire_nonregression=wire_nonreg,CPD_nonregression=cpd_nonreg,CPD_ns=t['candidate_CPD_ns'],ignored_fixups=c['fixups'],original_zero_counter_gate_pass=c['original_zero_counter_gate_pass'],query_seconds=model['all_query_seconds'],original_serialization_seconds=s['original_serialization_seconds'],indexed_serialization_seconds=s['indexed_serialization_seconds']))
  for p in [tp,sp,cp,mp]:bindings[str(p)]=sha(p)
 Q=R/'experiments/mmc_reference_repair_cold_quality_screen_v1_2026-10-19';qp=Q/'independent_primary_verification_v1.json';q=json.loads(qp.read_text())
 for p,h in q['bindings'].items():assert sha(p)==h
 bindings[str(qp)]=sha(qp);bindings[str(pathlib.Path(__file__).resolve())]=sha(__file__)
 result=dict(status='ALL3_NATIVE_PHYSICAL_MODEL_TRACE_COMPLETE_QOR_REPORTED',cases=rows,all3_native_wire_CPD_nonregression=all(x['wire_nonregression'] and x['CPD_nonregression'] for x in rows),all3_original_zero_counter_gate_pass=all(x['original_zero_counter_gate_pass'] for x in rows),original_prediction_quality_gate_pass=q['original_full_gate_pass'],original_prediction_quality_status=q['original_gate_status'],promote_default=False,bindings=bindings,scope='Exposed MMC development data only. Diagnostic reference-local slack budgets; actual default-constraint CPD nonregression is not setup closure. Original zero-counter gate unchanged. Original predictor gate unchanged. No unseen-family, matched full-workflow speedup or physical-board evidence. Single component serialization observations are not end-to-end timings.',next_action='Do not promote based on legal completion. Use complete all3 quality/cost evidence to decide next mechanism; avoid tuning exposed cases, budgets or quality thresholds to pass.')
 (O/'review.json').open('x').write(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ['bindings','cases','scope','next_action']},flush=True)
if __name__=='__main__':main()
