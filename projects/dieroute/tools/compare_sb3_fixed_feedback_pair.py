"""Compare six independently reviewed fixed SB3 feedback runs without adoption."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/sb3_fixed_feedback_pair_20261015'
def main():
 refs={}
 def digest(f):
  key=str(f)
  if key not in refs:refs[key]=hashlib.sha256(Path(f).read_bytes()).hexdigest()
  return refs[key]
 def read(f):digest(f);return json.loads(Path(f).read_text())
 def verify(d):
  for f,h in d.get('source_sha256',{}).items():assert digest(f)==h,f
 audit=read(P/'independent_audit.json');verify(audit)
 assert audit['status']=='six_fixed_feedback_pair_runs_independently_reviewed'
 assert len(audit['outcomes'])==6
 protocol=read(P/'protocol.json');verify(protocol);rows=[]
 for c in protocol['cases']:
  case=c['label'];off=next(x for x in audit['outcomes'] if (x['case'],x['arm'])==(case,'feedback_off'));on=next(x for x in audit['outcomes'] if (x['case'],x['arm'])==(case,'feedback_on'))
  recipes=[read(P/'recipes'/case/arm/'pair.json')['steps'][0] for arm in ['feedback_off','feedback_on']]
  env=[dict(v['routing_environment']) for v in recipes]
  assert [v.pop('DIEROUTE_CRITICAL_FEEDBACK_THRESHOLD_Q') for v in env]==['0','64880'] and env[0]==env[1]
  assert recipes[0]['command']==recipes[1]['command'] and recipes[0]['cwd']==recipes[1]['cwd']
  runs=[P/'native_runs'/(case+'_'+arm+'_0') for arm in ['feedback_off','feedback_on']]
  route=[read(d/'route.json') for d in runs]
  assert [v['criticality_feedback_threshold_q'] for v in route]==[0,64880]
  compatibility=read(runs[0]/'parent_scale1_compatibility.json')
  assert compatibility['status']=='fresh_remaining_tail_scale1_matches_completed_parent'
  # Legacy receipt names are inherited from the pre-frozen runner; actual scale is256.
  assert all(v['cost_scale']==256 and v['route_tree_timing_weight_q']==128 for v in route)
  rows.append(dict(case=case,feedback_off=off,feedback_on=on,feedback_events=route[1]['critical_feedback_events'],wirelength_delta=None if off['wirelength'] is None or on['wirelength'] is None else on['wirelength']-off['wirelength'],cpd_delta_ns=None if off['cpd_ns'] is None or on['cpd_ns'] is None else on['cpd_ns']-off['cpd_ns'],model_crossing_delta=on['model_crossings']-off['model_crossings'],iteration_delta=on['iterations']-off['iterations']))
 assert len(rows)==3
 digest(Path(__file__).resolve())
 report=dict(status='three_fresh_SB3_feedback_pairs_compared',outcomes=rows,feedback_off_joint_passes=sum(v['feedback_off']['joint_gate_pass'] for v in rows),feedback_on_joint_passes=sum(v['feedback_on']['joint_gate_pass'] for v in rows),source_sha256=refs,adopted=False,board_result=False,research_complete=False,scope='Three fixed development cases, one fresh off/on pair each, sole setting changed is existing feedback threshold0/64880. Archived off controls independently matched. Quality thresholds unchanged; no heldout, repeat statistics or physical claim. Legacy compatibility receipt filename mentions scale1 although verified actual costscale256.')
 with (P/'comparison_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ['outcomes','source_sha256']}))
if __name__=='__main__':main()
