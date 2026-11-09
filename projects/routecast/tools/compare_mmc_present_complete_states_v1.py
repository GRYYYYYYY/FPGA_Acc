"""Compare independently certified endogenous states; estimate differences, not native QoR."""
import json
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]

def main():
 out=R/'experiments/mmc_present_guard_complete_v1_2026-10-10'
 new=out/'model';old=R/'experiments/mmc_resident_manifest_scope_seed_handoff_v1_2026-10-10/model'
 proof=out/'verification.json';v=json.loads(proof.read_text())
 assert v['complete_115572_connections_and_independent_physical_events_pass']
 bindings={**v['bindings'],str(proof):sha(proof),str(Path(__file__).resolve()):sha(Path(__file__))}
 baseline=old/'shared_audit_receipt.json';b=json.loads(baseline.read_text())
 assert b['all_three_complete_audits_pass'];bindings.update(b['bindings']);bindings[str(baseline)]=sha(baseline)
 assert all(sha(p)==h for p,h in bindings.items())
 frames=[]
 for name in ['initial','sketch']:
  paths=[old/(name+'.json'),new/(name+'.json')]
  a,c=[json.loads(p.read_text()) for p in paths]
  for p in paths:bindings[str(p)]=sha(p)
  aa={x['connection_id']:x for x in a['records']};cc={x['connection_id']:x for x in c['records']}
  assert len(aa)==len(cc)==115572 and aa.keys()==cc.keys()
  counts=Counter();oldsum=newsum=0
  for cid,x in aa.items():
   y=cc[cid]
   for key in ['source','sink','net_id','floor_integer','budget_integer']:assert x[key]==y[key]
   dx=x['answer']['delay'];dy=y['answer']['delay']
   assert dx<=x['budget_integer'] and dy<=y['budget_integer']
   oldsum+=dx;newsum+=dy
   counts['changed_paths']+=x['answer']['physical_edge_ids']!=y['answer']['physical_edge_ids']
   counts['raw_delay_lower' if dy<dx else 'raw_delay_higher' if dy>dx else 'raw_delay_equal']+=1
  la={int(k):val for k,val in a['ledger'].items()};lc={int(k):val for k,val in c['ledger'].items()}
  frames.append(dict(frame=name,counts=dict(counts),original_overflow=a['overflow_units'],candidate_overflow=c['overflow_units'],original_sum_connection_raw_integer=oldsum,candidate_sum_connection_raw_integer=newsum,ledger_l1_difference=sum(abs(la.get(n,0)-lc.get(n,0)) for n in la.keys()|lc.keys())))
 assert all(sha(p)==h for p,h in bindings.items())
 (out/'state_comparison.json').write_text(json.dumps(dict(bindings=bindings,frames=frames,scope='Same exposed MMC endpoints, floors and budgets; independently certified own endogenous price trajectories. Raw-sum and overuse are demand-model diagnostics, not native critical path, hotspot accuracy, routeability or wholeworkflow speed.'),indent=2)+'\n')
 print(json.dumps(frames),flush=True)
if __name__=='__main__':main()
