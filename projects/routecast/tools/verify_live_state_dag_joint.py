"""Bind both native logs independently to retrospective joint decisions."""
import json,re
from pathlib import Path
from fractions import Fraction as F
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/live_state_dag_screen_replay_2026-10-07'
p=base/'joint_decision_evaluation.json';r=json.loads(p.read_text());assert all(sha(f)==h for f,h in r['bindings'].items())
cp=ROOT/'experiments/mux_full_cohort_cold_lifecycle_2026-10-06/receipt.json';cv=cp.parent/'verification.json';c=json.loads(cp.read_text());assert json.loads(cv.read_text())['receipt_sha256']==sha(cp)
op=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/receipt.json';o=json.loads(op.read_text());old={x['width']:x for x in o['rows']};rows=[];bindings={str(f):sha(f) for f in (p,cp,cv,op)}
for x,n in zip(r['rows'],c['rows']):
 w,i=x['width'],x['index'];assert (w,i)==(n['width'],n['index']);candidate=n['rounds'][0]['reload'];published=old[w]
 wire=[]
 for record in (published,candidate):
  assert record['exit_code']==0 and record['mismatches']==record['fixups']==0
  log=next(Path(f) for f in record['files'] if f.endswith('/reload.log'))
  assert sha(log)==record['files'][str(log)];bindings[str(log)]=sha(log)
  wire.append(int(re.findall(r'Total wirelength:\s*(\d+)',log.read_text())[-1]))
 assert wire==[x['published_wirelength'],x['candidate_wirelength']]
 joint=F(str(candidate['cpd_ns']))<=F(str(published['cpd_ns'])) and wire[1]<=wire[0]
 assert joint==x['native_joint_nonregression']==x['model_joint_admitted']
 rows.append(dict(width=w,index=i,published_cpd_ns=str(published['cpd_ns']),candidate_cpd_ns=str(candidate['cpd_ns']),joint_nonregression=joint))
result=dict(source_sha256=sha(Path(__file__)),bindings=bindings,rows=rows,cases=len(rows),joint_nonregressions=sum(x['joint_nonregression'] for x in rows),scope='Native rounded CPD and wire logs independently match joint retrospective classification. Candidate snapshots are cold routed, not newly generated RouteCast incremental candidates. No prospective/netgain claim.')
(base/'joint_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(rows)
