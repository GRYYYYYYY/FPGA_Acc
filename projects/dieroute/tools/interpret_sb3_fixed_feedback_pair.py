"""Interpret the complete predeclared feedback study; never certify research completion."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/sb3_fixed_feedback_pair_20261015'
def main():
 refs={}
 def digest(f):
  key=str(f)
  if key not in refs:refs[key]=hashlib.sha256(Path(f).read_bytes()).hexdigest()
  return refs[key]
 def read(f):digest(f);return json.loads(f.read_text())
 comparison=read(P/'comparison_audit.json')
 assert comparison['status']=='three_fresh_SB3_feedback_pairs_compared'
 for f,h in comparison['source_sha256'].items():assert digest(f)==h,f
 assert {v['case'] for v in comparison['outcomes']}=={'ex5p','diffeq','alu4'} and len(comparison['outcomes'])==3
 on_passes=sum(v['feedback_on']['joint_gate_pass'] for v in comparison['outcomes']);off_passes=sum(v['feedback_off']['joint_gate_pass'] for v in comparison['outcomes'])
 assert (off_passes,on_passes)==(comparison['feedback_off_joint_passes'],comparison['feedback_on_joint_passes'])
 failed=[dict(case=v['case'],failed_checks=[k for k,ok in v['feedback_on']['checks'].items() if not ok]) for v in comparison['outcomes'] if not v['feedback_on']['joint_gate_pass']]
 assert all(v['failed_checks'] for v in failed)
 protocol=read(P/'protocol.json');assert protocol['repeats']==1
 for case in protocol['cases']:
  for arm in protocol['arms']:
   recipe=read(P/'recipes'/case['label']/arm['label']/'pair.json');env=recipe['steps'][0]['routing_environment']
   assert env['DIEROUTE_MAX_ITERATIONS']=='30' and env['DIEROUTE_MIN_TIMING_ITERATIONS']=='3'
 digest(Path(__file__).resolve())
 result=dict(status='fixed_feedback_does_not_close_joint_development_quality_gate' if failed else 'all_three_single_repeat_development_quality_checks_pass_repeats_and_remaining_gates_open',feedback_off_joint_passes=off_passes,feedback_on_joint_passes=on_passes,failed_feedback_on_cases=failed,source_sha256=refs,adopted=False,research_complete=False,board_result=False,decision='Do not adopt or open heldout cases from this study. Retain all results and original quality thresholds. Further decisions must account for full three-case comparison and independent hardware/runtime gates.',scope='Predeclared SB3/cw80 remainingtail1 scale256 seed128 feedback0/64880, one fresh paired run per development case. No threshold search, repeat statistics, heldout validation, end-to-end speedup or physical performance result. Passing or failing this single study does not close G1-G8.')
 with (P/'interpretation.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))
if __name__=='__main__':main()
