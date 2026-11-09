"""Independent node-owner set cardinality reconciliation of conditional forecasts."""
import json
from pathlib import Path
from audit_prince_other_owner_transport_v1 import load,sha,D,R
O=R/'experiments/prince_conditional_two_frame_v1_2026-10-20'
def inverse(path):
 i,owners,_=load(path);nodes={}
 for net,group in owners.items():
  for node in group:nodes.setdefault(node,set()).add(net)
 return i,nodes
def main():
 source=O/'verification.json';v=json.loads(source.read_text());expected={(x['case'],x['iteration']):x for x in v['rows']};checked=0
 for case in v['cases']:
  paths=sorted((D/case/'capture/owners').glob('*.bin'),key=lambda p:int(p.stem.split('_')[-1]));previous=None;current=inverse(paths[0])
  for path in paths[1:]:
   future=inverse(path);i,a=current;b=previous[1] if previous else a;c=future[1];q=0;err=[0,0];exact=[0,0]
   for node,nets in a.items():
    old=b.get(node,set());new=c.get(node,set())
    for net in nets:
     now_other=len(nets-{net});old_other=len(old-{net});truth=2*len(new-{net})
     for k,pred in enumerate([2*now_other,now_other+old_other]):err[k]+=abs(pred-truth);exact[k]+=pred==truth
     q+=1
   row=expected[case,i];assert [q,*err,*exact]==[row[k] for k in ['queries','persistence_abs_error_half_units','two_frame_abs_error_half_units','persistence_exact','two_frame_exact']];checked+=q
   previous,current=current,future
 assert checked==v['totals']['queries'];p=O/'independent_verification_v1.json';assert not p.exists();p.write_text(json.dumps(dict(status='ALL_QUERY_SCORES_RECONCILED',queries=checked,pairs=len(expected),method='per-node NET owner-set cardinalities with explicit queried NET removal; no predictor imports',bindings={str(source):sha(source),str(Path(__file__)):sha(__file__)}),indent=2)+'\n');print('INDEPENDENT_CONDITIONAL_DEMAND_PASS',checked)
if __name__=='__main__':main()
