"""Authenticate all full-model proof gates and report bounded comparison scope."""
import json
import sys
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
name=sys.argv[1]
D=R/'experiments/resident_hybrid_complete_v5_2026-10-08'/name
def load(p):return json.loads(p.read_text())
r,p=load(D/'receipt.json'),load(D/'protocol.json')
assert r['status']=='COMPLETE_PROSPECTIVE_HYBRID_VERIFIED' and r['bindings']==p['bindings']
bindings={**r['bindings'],str(D/'receipt.json'):sha(D/'receipt.json'),str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__)):sha(Path(__file__))}
for path,h in r['proofs'].items():
    assert sha(path)==h
    proof=load(Path(path));assert all(sha(k)==v for k,v in proof['bindings'].items())
    bindings.update(proof['bindings']);bindings[path]=h
out=D/'resident';model=load(out/'receipt.json')
ep=load(next(Path(k) for k in model['bindings'] if k.endswith('/endpoints.json')))
count=len(ep['connections'])
initial,final=load(out/'initial_physical_verification.json'),load(out/'sketch_physical_verification.json')
events=load(out/'verification.json')
for proof in [initial,final,events]:
    assert proof['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
    assert proof['completed']==count
assert events['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass']
assert len(model['rounds'])==2
total=sum(len(row['events']) for row in model['rounds'])
committed=sum(e['status']=='COMMITTED' for row in model['rounds'] for e in row['events'])
assert total==events['events'] and committed==events['committed'] and total-committed==events['retained']
old=R/'experiments/resident_radix_count_complete_v4_2026-10-08'/name
assert load(out/'floors.json')==load(old/'floors.json') and r['all_original_zero_price_floors_equal']
old_model=load(old/'receipt.json')
for section in ['bindings','files']:
    assert all(sha(k)==h for k,h in old_model[section].items())
overflow=[initial['overflow_units'],*[row['overflow_after'] for row in model['rounds']]]
assert overflow==r['overflow'] and overflow[-1]==final['overflow_units']==events['overflow_units']
assert r['model_paid_seconds']==model['total_paid_resident_seconds']>0
result=dict(bindings=bindings,complete_prospective_hybrid_model_pass=True,completed=count,
            events=total,committed=committed,retained=total-committed,all_original_zero_price_floors_equal=True,
            overflow=overflow,old_overflow=[old_model['rounds'][0]['overflow_before'],*[x['overflow_after'] for x in old_model['rounds']]],
            candidate_single_model_paid_seconds=r['model_paid_seconds'],old_single_model_paid_seconds=old_model['total_paid_resident_seconds'],
            scope='Complete new prospective model physical states and event replay. Retained attempts have no independent weighted infeasibility certificate. Single model timings exclude subsequent independent audits; different runs are not paired performance. No native joint QoR, heldout family, end-to-end net gain, HDL or hardware proof.')
assert all(sha(k)==h for k,h in bindings.items())
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2))
