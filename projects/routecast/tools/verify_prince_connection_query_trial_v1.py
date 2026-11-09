"""Join exact connection-entry contexts to observed scalar-cost calls."""
import json
from collections import Counter,defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from verify_prince_native_query_trial_v1 import f32,value,bits
R=Path(__file__).resolve().parents[1];D=R/'experiments/prince_connection_query_trial_v1_2026-10-20'
def main():
 p=D/'verification.json';v=json.loads(p.read_text());assert len(v['rows'])==18;assert all(x['callback_sequence_complete'] and x['nonclock_iteration_summaries_equal'] and x['terminal_physical_sequences_equal'] for x in v['rows']);bindings={str(p):sha(p),str(__file__):sha(__file__)};rows=[]
 for case in sorted(x['case'].rsplit('/',1)[0] for x in v['rows'] if x['case'].endswith('/capture')):
  d=D/case/'capture';record=next(x for x in v['rows'] if x['case']==case+'/capture');mp=R/'experiments/prince_resident_consumer_v1_2026-10-20'/case/'NET_mapping.json';mapping={x['native_NET_id']:x['endpoint_NET_id'] for x in json.loads(mp.read_text()) if not x['ignored_global']};ep=R/'experiments/prince_native_cohort_v1_2026-10-20'/case/'pre_route_endpoints.json';targets=defaultdict(list)
  for x in json.loads(ep.read_text())['connections']:targets[x['net_id']].append(x['sink'])
  cp=d/'queries.tsv.connections.tsv';qp=d/'queries.tsv';contexts={}
  for line in cp.open():
   iteration,ident,net,pin,sink,nodes=map(int,line.split());assert ident not in contexts and net in mapping and 1<=pin<=len(targets[mapping[net]]) and sink in targets[mapping[net]] and nodes>0;contexts[ident]=(iteration,net,pin,sink)
  assert sorted(contexts)==list(range(1,len(contexts)+1));calls=groups=active=unscoped=owned=scalar=0;seen=set();periteration=Counter()
  for line in qp.open():
   iteration,encoded,node,kind,occ,cap,pres,acc,base,cost,nc,inside,ident,pin,sink,owns,count=map(int,line.split());groups+=1;calls+=count;periteration[iteration]+=count;assert owns in [0,1] and count>0
   if inside:
    assert contexts[ident]==(iteration,encoded-1,pin,sink);assert occ>=owns;active+=count;seen.add(ident);owned+=count*owns
   else:unscoped+=count
   if not nc:
    present=f32(1.+f32(value(pres)*(occ+1-cap))) if occ>=cap else 1.;assert bits(f32(f32(value(base)*value(acc))*present))==cost;scalar+=count
  for path in [cp,qp]:assert sha(path)==record['files'][str(path)];bindings[str(path)]=sha(path)
  for path in [mp,ep]:bindings[str(path)]=sha(path)
  prior=json.loads((R/'experiments/prince_native_query_trial_v1_2026-10-20/query_verification_v1.json').read_text());old=next(x for x in prior['rows'] if x['case']==case);assert calls==old['cost_calls'];assert unscoped==0 and scalar==calls
  rows.append(dict(case=case,connections=len(contexts),connections_with_cost_calls=len(seen),cost_calls=calls,connection_scoped_calls=active,unscoped_calls=unscoped,entry_tree_owned_node_calls=owned,unique_query_state_groups=groups,scalar_verified_calls=scalar,prior_cost_call_count_equal=True));print('CONNECTION_QUERY_CASE_PASS',case,calls,len(contexts),flush=True)
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items());out=D/'connection_query_verification_v1.json';assert not out.exists();out.write_text(json.dumps(dict(status='ALL_OBSERVED_COST_CALLS_HAVE_EXPLICIT_CONNECTION_CONTEXT',rows=rows,bindings=bindings,scope='Owned native entry RAII captures ConnectionParameters NET/pin and sink, joins sink membership/fanout to independent pre-route endpoints. Pin-index-to-specific-sink ordering not independently proven. Entry-tree membership is actual passed root subtree snapshot, not a full independently rebuilt current ledger. Cross-object cost-call coverage matches prior run counts, not proof of every same-object/inlined path. No release subtraction, price mutation, predictive/native/fullpaid gain.'),indent=2)+'\n')
if __name__=='__main__':main()
