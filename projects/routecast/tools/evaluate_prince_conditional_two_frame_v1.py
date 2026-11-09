"""Development next-iteration diagnostic, not original final-occupancy gate."""
import json
from pathlib import Path
from audit_prince_other_owner_transport_v1 import load,sha,D,R
from prince_conditional_two_frame_v1 import predict
O=R/'experiments/prince_conditional_two_frame_v1_2026-10-20'
def main():
 assert not O.exists();O.mkdir()
 source=D/'ownership_verification_v1.json';proof=json.loads(source.read_text());bindings={str(source):sha(source)}
 for name in ['prince_conditional_two_frame_v1.py','evaluate_prince_conditional_two_frame_v1.py','audit_prince_other_owner_transport_v1.py']:
  p=R/'tools'/name;bindings[str(p)]=sha(p)
 protocol=dict(method='unfitted mean of current and previous perNET membership indicators, summed over all OTHER NETs; first frame uses persistence',query_domain='current NET-owned CHANNEL nodes only',horizon='next native end-iteration ownership ledger',controls=['current coherent other-owner demand persistence'],score='absolute error in half-count integer units; exact-match counts; pooled and per-case',limitations='Exposed PRINCE development trajectories; adjacent-frame diagnostic only, not final occupancy quality/native utility/fullpaid gate. No search-candidate universe or native partial-release parity.',bindings=bindings)
 (O/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for case_row in proof['rows']:
  case=case_row['case'];paths=sorted((D/case/'capture/owners').glob('*.bin'),key=lambda p:int(p.stem.split('_')[-1]));previous=None;current=load(paths[0])
  for p in paths:assert sha(p)==proof['bindings'][str(p)];bindings[str(p)]=sha(p)
  for nextpath in paths[1:]:
   i,own,counts=current
   candidate=predict(own,counts,previous[1] if previous else None,previous[2] if previous else None)
   # Predictions fixed before loading the future frame.
   j,future,fc=load(nextpath);assert j==i+1
   errors=[0,0];matches=[0,0]
   for (net,node),estimate in candidate.items():
    truth=2*(fc[node]-int(node in future[net]));baseline=2*(counts[node]-1)
    assert truth>=0
    for k,value in enumerate([baseline,estimate]):errors[k]+=abs(value-truth);matches[k]+=value==truth
   rows.append(dict(case=case,iteration=i,next_iteration=j,queries=len(candidate),persistence_abs_error_half_units=errors[0],two_frame_abs_error_half_units=errors[1],persistence_exact=matches[0],two_frame_exact=matches[1]))
   previous,current=current,(j,future,fc)
 assert len(rows)==218
 keys=['queries','persistence_abs_error_half_units','two_frame_abs_error_half_units','persistence_exact','two_frame_exact'];totals={k:sum(row[k] for row in rows) for k in keys};cases={case:{k:sum(row[k] for row in rows if row['case']==case) for k in keys} for case in sorted({row['case'] for row in rows})}
 assert all(sha(p)==h for p,h in bindings.items());(O/'verification.json').write_text(json.dumps(dict(rows=rows,totals=totals,cases=cases,bindings=bindings,status='DEVELOPMENT_CONDITIONAL_DEMAND_SCREEN_COMPLETE_NOT_PROMOTED'),indent=2)+'\n');print(json.dumps(dict(totals=totals,cases=cases)))
if __name__=='__main__':main()
