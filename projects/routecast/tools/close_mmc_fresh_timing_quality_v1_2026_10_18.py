"""Close prospectively frozen three-placement V2 quality cohort honestly."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
Q=R/'experiments/mmc_fresh_timing_quality_v1_2026-10-18';N=R/'experiments/mmc_multiplacement_cold_labels_v1_2026-10-18';F=R/'experiments/mmc_fresh_timing_feedback_v1_2026-10-18/protocol.json';frozen=json.loads(F.read_text());assert frozen['case_order']==['case_01','case_02','case_03'];bindings={**closure([Path(__file__)]),str(F):sha(F)};rows=[]
for case in frozen['case_order']:
 D=Q/case;vp=D/'verification.json';rp=D/'comparison.json';pp=D/'protocol.json';v=json.loads(vp.read_text());r=json.loads(rp.read_text());p=json.loads(pp.read_text());assert v['status']=='pass' and v['histogram_rank_topk_mae_checks']==12 and v['primary_gate_pass']==r['primary_gate_pass'];assert v['bindings'][str(rp)]==sha(rp);assert r['bindings'][str(pp)]==sha(pp);assert p['frozen_cohort_protocol_sha256']==sha(F);assert p['primary_candidate']=='native_retained_fresh_timing_on' and p['primary_controls']==['native_retained_on','raw_min_on','previous_native'];assert all(v['bindings'][k]==h for k,h in r['bindings'].items());assert sha(D/'vectors.json')==r['bindings'][str(D/'vectors.json')];assert r['complete_positive_channel_universe']==258720 and r['complete_span_bin_universe']==17160
 checks=[]
 for control in p['primary_controls']:
  cm=[]
  for scope in ['concrete','spatial']:
   for metric in ['spearman','precision_at_k']:
    baseline=r['metrics']['cold'][control][scope][metric];candidate=r['metrics']['cold'][p['primary_candidate']][scope][metric];eps=1e-12 if metric=='spearman' else 0
    cm.append(dict(scope=scope,metric=metric,reference=baseline,candidate=candidate,nonregression=baseline is not None and candidate is not None and candidate>=baseline-eps,strict_improvement=baseline is not None and candidate is not None and candidate>baseline+eps))
  checks.append(dict(label='cold',control=control,comparisons=cm,pass_primary_gate=all(x['nonregression'] for x in cm) and any(x['strict_improvement'] for x in cm)))
 assert checks==r['primary_checks'] and all(x['pass_primary_gate'] for x in checks)==r['primary_gate_pass'];rows.append(dict(case=case,primary_gate_pass=r['primary_gate_pass'],checks=checks,metrics=r['metrics']['cold']))
 for file in [vp,rp,pp,D/'vectors.json']:bindings[str(file)]=sha(file)
for case in frozen['case_order']:
 nativeproof=N/case/'verification.json';nv=json.loads(nativeproof.read_text());assert nv['all_native_physical_and_canonical_pass'];assert len(nv['rows'])==1;canonical=nv['rows'][0]['canonical'];assert canonical['semantic_consistency_gate_pass'] and canonical['fixups']==330 and canonical['original_zero_counter_gate_pass'] is False;bindings[str(nativeproof)]=sha(nativeproof)
np=N/'cohort_complete.json';assert json.loads(np.read_text())['all3_cold_labels_admitted'];diag=N/'global_rerouting_diagnostic_v1.json';dv=N/'rerouting_union_independent_verification_v2.json';d=json.loads(diag.read_text());iv=json.loads(dv.read_text());assert iv['status']=='pass' and iv['bindings'][str(diag)]==sha(diag)
for file in [np,diag,dv]:bindings[str(file)]=sha(file)
assert all(sha(p)==h for p,h in bindings.items())
result=dict(status='closed_verified',bindings=bindings,case_count=3,independently_checked_metric_vectors=36,rows=rows,cohort_primary_gate_pass=all(x['primary_gate_pass'] for x in rows),actual_native_rerouting=d['rows'],independent_NET_union_lower_bounds=iv['rows'],decision='Do not promote fresh-timing-only policy from exposed mechanism results. Compare all cases to endpoint retained_on, raw_min_on and old footprint; lower overflow is insufficient. No case or control switching based on these labels.',next_research='Use this isolated fresh-input comparison to assess stale-criticality contribution. Preserve the forecast-quality failures. Independently evaluate native seed utility of the already physically audited V2retained_off/on states before claiming value or optimizing more kernels; any full-flow gain requires fresh matched accounting, and unseen-quality/hardware requirements remain open.',scope='Only-fresh-criticality mechanism trial on three already exposed swaps; all native labels were previously seen. Not a fresh promotion or independent-family/heldout experiment. Native labels admitted with330ignored pin fixups; original zero-counter gate false. No candidate native QoR, fresh continuous workflow gain, FPGA/RTL/board or all-old minimum dual claim.')
with (Q/'cohort_research_decision_v1.json').open('x') as out:json.dump(result,out,indent=2)
print('COHORT CLOSED',result['cohort_primary_gate_pass'],'36 independent metric vectors',[(x['case'],x['primary_gate_pass']) for x in rows],flush=True)
