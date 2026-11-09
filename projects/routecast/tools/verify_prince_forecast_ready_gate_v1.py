"""Boundary fixtures and independent adjacent-pair replay of fixed readiness rule."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from prince_forecast_ready_gate_v1 import ReadyGate
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_forecast_ready_replay_v1_2026-10-20'
def main():
 identity={'case':'fixture','config':'fixed'};fixtures=[([1,1,1,1],3),([0,2,1,1],4),([0,0,2,1,1],5),([2,2,2,2],None),([1,1,1,1,1],3)];positive=0
 for counts,expected in fixtures:
  c=ReadyGate(identity);events=[i for i,n in enumerate(counts,1) if c.observe(identity,i,100,n)];assert events==([] if expected is None else [expected]);positive+=1
 negative=0
 for wrong in [('identity',{'case':'other'},1,100,0),('sequence',identity,2,100,0),('empty',identity,1,0,0),('over',identity,1,100,101),('negative',identity,1,100,-1),('bool',identity,True,100,0)]:
  name,tag,i,n,over=wrong;c=ReadyGate(identity)
  try:c.observe(tag,i,n,over)
  except ValueError:negative+=1;assert c.iteration==0
  else:raise AssertionError(name)
 dp=D/'decisions.json';v=json.loads(dp.read_text());root=E/'prince_configured_consumer_trial_v1_2026-10-20';rows=[];bindings={str(p):sha(p) for p in [dp,Path(__file__),R/'tools/prince_forecast_ready_gate_v1.py']}
 for row in v['rows']:
  p=root/row['case']/'digest/callback.tsv';values=[list(map(int,s.split())) for s in p.read_text().splitlines()];pairs=[values[i][0] for i in range(1,len(values)) if values[i-1][0]>=2 and 100*values[i-1][4]<=values[i-1][1] and 100*values[i][4]<=values[i][1]];expected=min(pairs) if pairs else None;assert expected==row['selected_iteration'];assert sum(x['ready_event'] for x in row['events'])==int(expected is not None);rows.append(dict(case=row['case'],selected_iteration=expected));bindings[str(p)]=sha(p)
 assert positive==5 and negative==6 and len(rows)==9 and all(sha(p)==h for p,h in bindings.items());(D/'independent_rule_verification_v1.json').write_text(json.dumps(dict(status='FIXED_READY_RULE_FIXTURES_AND_ALL9_INDEPENDENT_PAIR_REPLAYS_PASS',positive_fixtures=positive,negative_fixtures=negative,rows=rows,bindings=bindings,scope='Integer threshold, consecutive observations, one-shot event and identity/sequence/domain rejection. Offline replay only, no live emission, native stopping or prefix cost claim.'),indent=2)+'\n');print('READY_GATE_CONTRACT_PASS',positive,negative,len(rows))
if __name__=='__main__':main()
