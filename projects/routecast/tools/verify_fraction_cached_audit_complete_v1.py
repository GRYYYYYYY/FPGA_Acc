"""Independent complete-case proof/copy authentication and full field comparison."""
import json
import math
import sys
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
ROOT=R/'experiments/fraction_cached_audit_complete_v1_2026-10-08'
names=['xtea','8051','mmc'] if sys.argv[1]=='all' else [sys.argv[1]]
assert all(n in ['xtea','8051','mmc'] for n in names)
bindings={str(Path(__file__)):sha(Path(__file__))};cases=[]
def load(p):return json.loads(p.read_text())
def auth(d):
    for section in ['bindings','files','copies']:
        for path,h in d.get(section,{}).items():assert sha(path)==h,path
for name in names:
    D=ROOT/name;old=R/'experiments/resident_radix_count_complete_v4_2026-10-08'/name
    r,p=load(D/'receipt.json'),load(D/'protocol.json');auth(r);auth(p)
    assert r['bindings']==p['bindings'] and r['copies']==p['copies']
    assert r['all_three_complete_scientific_outputs_equal'] and len(r['rows'])==3
    assert {Path(x).name for x in r['copies']}=={'protocol.json','receipt.json','initial.json','sketch.json','floors.json','round0.json','round1.json'}
    for path,h in r['copies'].items():assert sha(old/Path(path).name)==h
    outputs=[D/'model_copy/initial_physical_verification_rc_cache_v4.json',D/'model_copy/sketch_physical_verification_rc_cache_v4.json',D/'events_cached.json']
    originals=['initial_physical_verification.json','sketch_physical_verification.json','verification.json']
    observations=[]
    for i,row in enumerate(r['rows']):
        assert row['stage']==i and row['complete_scientific_output_equal']
        assert Path(row['proof'])==outputs[i] and sha(outputs[i])==row['sha256']
        assert math.isfinite(row['seconds']) and row['seconds']>0
        a,b=load(outputs[i]),load(old/originals[i]);auth(a);auth(b)
        assert {k:v for k,v in a.items() if k!='bindings'}=={k:v for k,v in b.items() if k!='bindings'}
        assert a['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
        if i==2:assert a['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass']
        bindings.update(a['bindings']);bindings.update(b['bindings'])
        bindings[str(outputs[i])]=sha(outputs[i]);bindings[str(old/originals[i])]=sha(old/originals[i])
        observations.append(dict(stage=i,completed=a['completed'],seconds=row['seconds']))
    assert len({x['completed'] for x in observations})==1
    bindings.update(r['bindings']);bindings.update(r['copies'])
    bindings[str(D/'receipt.json')]=sha(D/'receipt.json');bindings[str(D/'protocol.json')]=sha(D/'protocol.json')
    cases.append(dict(name=name,all_three_complete_scientific_outputs_equal=True,stages=observations))
assert all(sha(path)==h for path,h in bindings.items())
result=dict(bindings=bindings,cases=cases,all_required_complete_cached_audits_scientifically_equal=True,
    all_three_design_cases_verified=names==['xtea','8051','mmc'],
    scope='Original complete proof fields exactly preserved, copies and all source/input/output bindings authenticated. Producer single cached clocks are not paired speed evidence; no model search, native QoR or workflow gain claim.')
out=ROOT if len(names)>1 else ROOT/names[0]
(out/'independent_verification_v1.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2))
