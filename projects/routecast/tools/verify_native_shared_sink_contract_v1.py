"""Independent scenario expectations for actual native own-index/alias behavior."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/native_shared_sink_contract_v3_2026-10-19';B=R/'build/native_shared_sink_contract_v3_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=json.loads((D/'protocol.json').read_text());assert all(sha(k)==h for k,h in p['bindings'].items());bindings={str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__).resolve()):sha(__file__)};results=[]
 scenarios=[dict(name='distinct sinks, only first eligible',alias=False,stable=False,flags=[True,False]),dict(name='shared sink, first eligible then ineligible',alias=True,stable=False,flags=[True,True]),dict(name='shared sink, ineligible then eligible',alias=True,stable=False,flags=[True,True]),dict(name='shared sink, both eligible',alias=True,stable=False,flags=[True,True]),dict(name='first own bound improves, second requests reroute',alias=True,stable=False,flags=[True,True]),dict(name='first own bound zero, second requests reroute',alias=True,stable=False,flags=[True,True]),dict(name='no eligible pin',alias=True,stable=True,flags=[False,False])]
 for arm in ('original','own_index_fixed','own_index_group_or'):
  f=D/(arm+'.tsv');observed={};resets={}
  for line in f.open():
   x=line.split();kind=x[0];scenario=int(x[1]);assert 0<=scenario<7
   if kind=='R':assert scenario not in observed;observed[scenario]=dict(alias=bool(int(x[2])),stable=bool(int(x[3])),flags=list(map(lambda v:bool(int(v)),x[4:])))
   elif kind=='Z':assert scenario not in resets;resets[scenario]=tuple(map(int,x[2:]));assert resets[scenario]==(1,0,0)
   else:raise ValueError(kind)
  assert set(observed)==set(resets)==set(range(7));fail=[]
  for i,expected in enumerate(scenarios):
   assert observed[i]['alias']==expected['alias']
   if any(observed[i][key]!=expected[key] for key in ('stable','flags')):fail.append(i)
  results.append(dict(arm=arm,semantic_mismatch_scenarios=fail,all7_reset_checks_pass=True,observed=observed));bindings[str(f)]=sha(f);bindings[str(B/arm)]=sha(B/arm)
 assert results[0]['semantic_mismatch_scenarios']==[0,1,5];assert results[1]['semantic_mismatch_scenarios']==[1];assert results[2]['semantic_mismatch_scenarios']==[]
 for f in (B/'fixture.cpp',B/'fixture.o',B/'connection_based_routing.cpp',B/'connection_based_routing.h',B/'group_or.o'):bindings[str(f)]=sha(f)
 assert all(sha(k)==h for k,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ACTUAL_NATIVE_SHARED_SINK_LOST_REQUEST_REPRODUCED_GROUP_OR_7_SCENARIOS_PASS',scenarios=scenarios,rows=results,bindings=bindings,scope='Synthetic Netlist/terminal fixtures execute actual compiled CBRR. Only scalar timing getter supplied by link wrap; no physical RR graph, route search, STA/canonical, QoR or utility acceptance. Original all3 cohort has no shared sinks.'),indent=2)+'\n');print(json.dumps([{k:v for k,v in r.items() if k!='observed'} for r in results]))
if __name__=='__main__':main()
