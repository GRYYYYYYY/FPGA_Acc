"""Compare predeclared zero-weight ablation with immutable weight128 parent."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/rr_remaining_tail_zero_seed_ablation_20261015';A=R/'work/rr_remaining_tail_precision_development_v2_20261015'
def main():
 new=json.loads((P/'independent_audit.json').read_text());old=json.loads((A/'independent_audit.json').read_text());rows=[];refs={}
 def bind(f):refs[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
 for row in new['outcomes']:
  case=row['case'];parent=next(v for v in old['outcomes'] if v['case']==case and v['arm']=='scale256')
  files=[P/'recipes'/case/'weight0_scale256/pair.json',A/'recipes'/case/'scale256/pair.json'];recipes=[json.loads(f.read_text())['steps'][0] for f in files]
  env=[dict(v['routing_environment']) for v in recipes];assert env[0].pop('DIEROUTE_TREE_TIMING_WEIGHT_Q')=='0' and env[1].pop('DIEROUTE_TREE_TIMING_WEIGHT_Q')=='128';assert env[0]==env[1]
  assert recipes[0]['command'][:3]==recipes[1]['command'][:3] and recipes[0]['command'][4:]==recipes[1]['command'][4:]
  for f in files:bind(f)
  rows.append(dict(case=case,weight0=row,weight128=parent,wirelength_delta=(row['wirelength']-parent['wirelength']) if row['wirelength'] is not None and parent['wirelength'] is not None else None,cpd_delta_ns=(row['cpd_ns']-parent['cpd_ns']) if row['cpd_ns'] is not None and parent['cpd_ns'] is not None else None))
 for f in [P/'independent_audit.json',A/'independent_audit.json',P/'protocol.json',Path(__file__).resolve()]:bind(f)
 report=dict(status='three_development_zero_seed_ablation_compared_to_frozen128parents',outcomes=rows,weight0_joint_passes=sum(v['weight0']['joint_gate_pass'] for v in rows),weight128_joint_passes=sum(v['weight128']['joint_gate_pass'] for v in rows),source_sha256=refs,adopted=False,board_result=False,research_complete=False,scope='Single predeclared factor, completed parent controls rather than fresh paired repeats. Native printed metrics and model crossings only; not general causality, heldout, physical or adoption evidence.')
 with (P/'comparison_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ('source_sha256','outcomes')}))
if __name__=='__main__':main()
