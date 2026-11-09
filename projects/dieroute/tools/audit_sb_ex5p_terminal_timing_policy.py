"""Bind terminal timing observations to executed policy; no counterfactual run."""
import csv,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/'work/sb_ex5p_terminal_timing_policy_20261015'
def main():
 P.mkdir(exist_ok=False);refs={}
 def read(p):
  refs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
  return json.loads(p.read_text())
 precision=read(R/'work/rr_remaining_tail_precision_development_v2_20261015/protocol.json')
 source=R/'work/rr_remaining_layer_tail_variant_20261015/source/dieroute'
 for p in [source/'host/rr_host.cpp',source/'src/wide_controller.cpp']:
  digest=hashlib.sha256(p.read_bytes()).hexdigest();assert precision['source_sha256'][str(p)]==digest;refs[str(p)]=digest
 host=(source/'host/rr_host.cpp').read_text();controller=(source/'src/wide_controller.cpp').read_text()
 assert 'connection.criticality_q=std::min(connection.criticality_q,criticality_cap)' in host
 assert 'old_criticalities[i]<feedback_threshold&&task.criticality_q>=feedback_threshold' in controller
 assert 'all&&over==0&&!force_timing_reroute&&!supplemental' in controller
 trajectory=read(R/'work/sb_ex5p_task895_timing_trajectory_20261015/independent_audit.json')
 results=[]
 for case in trajectory['outcomes']:
  label=case['case'];last=case['trajectory'][-1]
  if label=='weight128':
   pair=read(R/'work/rr_remaining_tail_precision_development_v2_20261015/recipes/ex5p/scale256/pair.json')
   cfg=pair['steps'][0]['routing_environment']
   assert cfg['DIEROUTE_CRITICAL_FEEDBACK_THRESHOLD_Q']=='0' and cfg['DIEROUTE_MIN_TIMING_ITERATIONS']=='3' and cfg['DIEROUTE_MAX_ITERATIONS']=='30'
  results.append(dict(case=label,terminal_iteration=last['iteration'],input_q=last['input_criticality_q'],raw_STA_output_q=last['output_criticality_q'],capped_output_q=min(64880,last['output_criticality_q']),observed_terminal_task_would_cross_cap=last['input_criticality_q']<64880<=min(64880,last['output_criticality_q'])))
 old=read(R/'work/rr_critical_feedback_variant_20261014/protocol.json')
 old_pair=read(R/'work/rr_critical_feedback_variant_20261014/feedback_comparison.json')
 assert old_pair['status']=='same_source_critical_feedback_pair_audited'
 assert any('native_ex5p_stratix2die_cw80_20261013' in x for x in old['commands'][0])
 assert [x['observed_terminal_task_would_cross_cap'] for x in results]==[True,False]
 refs[str(Path(__file__).resolve())]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 report=dict(status='terminal_task895_raw_STA_cap_and_crossing_policy_distinguished',outcomes=results,source_sha256=refs,old_feedback_coverage='Existing off/on study uses older stratix2die ex5p with cost_scale1; it is not an executed SB3/cost_scale256 feedback control.',scope='Observed crossings only. Enabling feedback changes earlier routes and one-use-per-net history, so neither terminal crossing eligibility nor counterfactual success is proved. A raw65535 STA output is capped64880 before controller use. No extra-iteration benefit, quality adoption, hardware result or bug claim.',adopted=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps(dict(status=report['status'],outcomes=results)))
if __name__=='__main__':main()
