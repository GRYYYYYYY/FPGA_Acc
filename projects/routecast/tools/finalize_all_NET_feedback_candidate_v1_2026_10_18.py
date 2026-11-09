"""Preserve all original quality failures; prohibit native promotion on any failed gate."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 E=R/'experiments';root=E/'mmc_all_NET_feedback_v1_2026-10-18';quality=E/'mmc_all_NET_feedback_quality_v1_2026-10-18';bindings=closure([Path(__file__)]);rows=[]
 def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
 def admit(p):
  d=load(p);assert all(sha(k)==h for k,h in d['bindings'].items());bindings.update(d['bindings']);return d
 audit=admit(root/'independent_audits/verification.json');assert audit['all3_full_frames_and_all_NET_event_replays_pass'];summary=admit(root/'intervention_summary.json');qr=admit(quality/'results.json')
 spec=admit(E/'mmc_all_NET_feedback_candidate_protocol_v1_2026-10-18/protocol.json')
 for case in ['case_01','case_02','case_03']:
  p=load(quality/case/'protocol.json');r=admit(quality/case/'comparison.json');v=admit(quality/case/'verification.json');assert v['status']=='pass' and v['histogram_rank_topk_mae_checks']==14 and v['truth_tie_interval_checks']==14;assert r['primary_gate_pass']==v['primary_gate_pass'];assert p['primary_candidate']=='all_NET_on' and p['primary_controls']==['raw_min_on','previous_native'];checks=r['primary_checks'];assert len(checks)==2 and {c['control'] for c in checks}=={'raw_min_on','previous_native'};assert all(c['label']=='cold' and len(c['comparisons'])==4 for c in checks);assert r['primary_gate_pass']==all(c['pass_primary_gate'] for c in checks)
  rows.append(dict(case=case,primary_gate_pass=r['primary_gate_pass'],primary_checks=checks,metrics=r['metrics']['cold'],interventions=next(x for x in summary['cases'] if x['case']==case)))
 passed=all(x['primary_gate_pass'] for x in rows);assert passed==qr['all3_original_cold_primary_gate_pass'];assert all(sha(k)==h for k,h in bindings.items())
 d=dict(status='original_cold_quality_pass_native_utility_still_unproven' if passed else 'original_cold_quality_failed_no_native_promotion',bindings=bindings,candidate=spec['candidate'],all3_original_cold_gate_pass=passed,native_policy_trial_executed=False,cases=rows,scope='All3 exposed development cases. Preserve every regression and original control. Lower model overflow alone is insufficient. Neither strict unseen-family generalization, accepted complete workflow speed gain nor hardware execution is established.',next_action='Audit source eligibility and prepare a separately fixed matched native utility protocol.' if passed else 'Retain this candidate as failed under original quality gate; do not tune rounds/guards/case selection on these labels or run native utility. Analyze residual forecast support before fixing a distinct source-only research hypothesis.')
 with (root/'research_decision_v1.json').open('x') as f:json.dump(d,f,indent=2)
 print(d['status'],flush=True)
if __name__=='__main__':main()
