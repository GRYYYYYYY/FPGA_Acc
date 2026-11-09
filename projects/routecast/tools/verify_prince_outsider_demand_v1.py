"""Node-to-owner set verification with independent cyclic NET selection."""
import json
from audit_prince_other_owner_transport_v1 import load,sha,D,R
O=R/'experiments/prince_outsider_demand_v1_2026-10-20'
def frame(p):
 i,owners,_=load(p);inv={}
 for net,nodes in owners.items():
  for node in nodes:inv.setdefault(node,set()).add(net)
 return i,sorted(owners),inv
def main():
 source=O/'verification.json';v=json.loads(source.read_text());expected={(x['case'],x['iteration']):x for x in v['rows']};checked=0
 for case in v['cases']:
  paths=sorted((D/case/'capture/owners').glob('*.bin'),key=lambda p:int(p.stem.split('_')[-1]));prev=None;cur=frame(paths[0])
  for p in paths[1:]:
   nxt=frame(p);i,nets,a=cur;b=prev[2] if prev else a;c=nxt[2];err=[0,0];exact=[0,0];entered=0
   for node,own in a.items():
    start=node%len(nets);order=nets[start:]+nets[:start];net=next(n for n in order if n not in own);old=len(b.get(node,set())-{net});current=len(own-{net});truth=2*len(c.get(node,set())-{net});entered+=net in c.get(node,set())
    for k,value in enumerate([2*current,current+old]):err[k]+=abs(value-truth);exact[k]+=value==truth
   row=expected[case,i];assert [len(a),entered,*err,*exact]==[row[k] for k in ['queries','queried_NET_enters_node_next_frame','persistence_abs_error_half_units','two_frame_abs_error_half_units','persistence_exact','two_frame_exact']];checked+=len(a);prev,cur=cur,nxt
 assert checked==v['totals']['queries'];p=O/'independent_verification_v1.json';assert not p.exists();p.write_text(json.dumps(dict(queries=checked,pairs=len(expected),status='ALL_OUTSIDER_SCORES_RECONCILED',method='independent cyclic selection and inverse owner-set cardinalities',bindings={str(source):sha(source),str(__file__):sha(__file__)}),indent=2)+'\n');print('OUTSIDER_INDEPENDENT_PASS',checked)
if __name__=='__main__':main()
