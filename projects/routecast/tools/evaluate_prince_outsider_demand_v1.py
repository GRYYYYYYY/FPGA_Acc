"""Input-only cyclic outsider queries; adjacent-frame development screen."""
import json
from audit_prince_other_owner_transport_v1 import load,sha,D,R
O=R/'experiments/prince_outsider_demand_v1_2026-10-20'
def queries(owners,counts):
 nets=sorted(owners);result=[]
 for node in sorted(counts):
  start=node%len(nets)
  for offset in range(len(nets)):
   net=nets[(start+offset)%len(nets)]
   if node not in owners[net]:result.append((net,node));break
  else:raise AssertionError('no outsider')
 return result
def main():
 assert not O.exists();O.mkdir();p=D/'ownership_verification_v1.json';proof=json.loads(p.read_text());bindings={str(p):sha(p),str(__file__):sha(__file__)}
 protocol={'query_rule':'One outsider per currently occupied CHANNEL: ascending native NET IDs, cyclic start nodeID modulo NET count, first NET not owning node. Future labels never select queries.','predictor':'Equal mean of current and previous coherent other-owner demand; first frame persistence.','horizon':'next end-iteration native ledger','control':'current coherent other-owner demand persistence','scope':'Exposed PRINCE development; arbitrary outsider need not be a reachable search candidate. No final-forecast or native utility claim.','bindings':dict(bindings)}
 (O/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for case_row in proof['rows']:
  case=case_row['case'];paths=sorted((D/case/'capture/owners').glob('*.bin'),key=lambda p:int(p.stem.split('_')[-1]));previous=None;current=load(paths[0])
  for p in paths:assert sha(p)==proof['bindings'][str(p)];bindings[str(p)]=sha(p)
  for path in paths[1:]:
   i,owners,counts=current;old_owners,old_counts=(previous[1],previous[2]) if previous else (owners,counts)
   domain=queries(owners,counts)
   predictions=[(net,node,2*counts[node],counts[node]+old_counts[node]-int(node in old_owners[net])) for net,node in domain]
   j,future,fc=load(path);assert j==i+1;err=[0,0];exact=[0,0];entered=0
   for net,node,baseline,candidate in predictions:
    truth=2*(fc[node]-int(node in future[net]));assert min(truth,candidate)>=0;entered+=node in future[net]
    for k,value in enumerate([baseline,candidate]):err[k]+=abs(value-truth);exact[k]+=value==truth
   rows.append(dict(case=case,iteration=i,queries=len(domain),queried_NET_enters_node_next_frame=entered,persistence_abs_error_half_units=err[0],two_frame_abs_error_half_units=err[1],persistence_exact=exact[0],two_frame_exact=exact[1]));previous,current=current,(j,future,fc)
 assert len(rows)==218;keys=[k for k in rows[0] if k not in ['case','iteration']];totals={k:sum(x[k] for x in rows) for k in keys};cases={case:{k:sum(x[k] for x in rows if x['case']==case) for k in keys} for case in sorted({x['case'] for x in rows})}
 assert all(sha(p)==h for p,h in bindings.items());(O/'verification.json').write_text(json.dumps(dict(rows=rows,totals=totals,cases=cases,bindings=bindings,status='OUTSIDER_DEVELOPMENT_SCREEN_COMPLETE'),indent=2)+'\n');print(json.dumps(dict(totals=totals,cases=cases)))
if __name__=='__main__':main()
