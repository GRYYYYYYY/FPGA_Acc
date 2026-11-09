"""Authenticate four timed arms, actual quality reports and comparison arithmetic."""
import json,statistics,math
from pathlib import Path
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'paired_direct_abba_v1_2026-10-09';rp=D/'verification.json';r=json.loads(rp.read_text());assert all(sha(p)==h for p,h in r['bindings'].items());mp=R/'tools/paired_direct_abba_manifest_v1.json';m=json.loads(mp.read_text());assert [x['mode'] for x in r['rows']]==['online','cold','cold','online'];bindings={**r['bindings'],**closure([Path(__file__)]),str(rp):sha(rp),str(mp):sha(mp)};identities=[]
for i,(row,plan) in enumerate(zip(r['rows'],m['plans'])):
 assert row['arm']==i and row['mode']==plan['mode'] and row['workflow_seconds']>0 and row['exit_codes']==[0]*len(plan['commands'])
 p=E/plan['report'];d=json.loads(p.read_text());assert all(sha(p)==h for p,h in d['bindings'].items());q=d['rows'][0] if row['mode']=='online' else d;assert q['native_and_canonical_connections']==[516,516] and q['exact_model_budget_pass'] and q['full_named_paths_preserved'] and q['canonical_zero_counters'];assert q['cpd_ns']==4.87739 and q['wirelength']==(2629 if row['mode']=='online' else 2646)
 planp=E/plan['native']/'protocol.json';native=json.loads(planp.read_text())['plans'][0];identities.append({k:native[k] for k in ['step','endpoints','budget','command']});bindings[str(p)]=sha(p);bindings[str(planp)]=sha(planp)
assert all(x==identities[0] for x in identities)
for name in ['design.blif','design.net','design.place']:assert len({sha(E/p['native']/'step_3'/name) for p in m['plans']})==1
online=statistics.mean(x['workflow_seconds'] for x in r['rows'] if x['mode']=='online');cold=statistics.mean(x['workflow_seconds'] for x in r['rows'] if x['mode']=='cold');assert math.isclose(online,r['online_mean_seconds']) and math.isclose(cold,r['cold_mean_seconds']) and math.isclose(online/cold,r['online_to_cold_ratio'])
assert all(sha(p)==h for p,h in bindings.items());out=dict(bindings=bindings,online_seconds=[x['workflow_seconds'] for x in r['rows'] if x['mode']=='online'],cold_seconds=[x['workflow_seconds'] for x in r['rows'] if x['mode']=='cold'],online_mean_seconds=online,cold_mean_seconds=cold,online_to_cold_ratio=online/cold,quality_gate_pass=True,conclusion='ONLINE_PROTOTYPE_COST_REGRESSION_ON_THIS_SINGLE_CASE' if online>cold else 'ONLINE_WORKFLOW_LOWER_COST_ON_THIS_SINGLE_CASE',scope=r['scope']);(D/'independent_verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='bindings'},indent=2))
