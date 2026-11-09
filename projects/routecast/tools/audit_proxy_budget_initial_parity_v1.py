"""Independent initial-state equality except frozen proxy-budget metadata."""
import math,struct
from fractions import Fraction
POLICY='original_budget_plus_ceil_one_minus_criticality_times_floor_v1'
def audit(candidate,baseline,pins):
    criticalities={};identities={};pin_keys=set();global_pins=set()
    old={x['connection_id']:x for x in baseline['records']};assert len(old)==len(baseline['records'])
    for row in pins:
        cid=row['connection_id'];key=(row['net'],row['local_sink_pin']);assert cid not in criticalities and key not in pin_keys and row['global_pin'] not in global_pins
        o=old[cid];assert (row['net'],row['source_rr'],row['target_rr'])==(o['net_id'],o['source'],o['sink'])
        c=Fraction(struct.unpack('<f',struct.pack('<f',float(row['criticality_float32_text'])))[0]);assert 0<=c<=1
        criticalities[cid]=c;identities[cid]=key;pin_keys.add(key);global_pins.add(row['global_pin'])
    assert set(criticalities)==set(old)
    assert {k:v for k,v in candidate.items() if k!='records'}=={k:v for k,v in baseline.items() if k!='records'}
    assert len(candidate['records'])==len(old)
    seen=set();changed=0
    for row in candidate['records']:
        cid=row['connection_id'];assert cid not in seen;seen.add(cid);o=old[cid]
        assert {k:v for k,v in row.items() if k!='budget_integer'}=={k:v for k,v in o.items() if k!='budget_integer'}
        expected=o['budget_integer']+math.ceil((1-criticalities[cid])*o['floor_integer'])
        assert type(row['budget_integer']) is int and row['budget_integer']==expected
        changed+=expected!=o['budget_integer']
    assert seen==set(old)
    return dict(connections=len(seen),changed_budgets=changed,initial_paths_floors_and_ledgers_preserved=True)
def protocol(candidate,baseline):
    assert candidate['budget_policy']==POLICY
    c={k:v for k,v in candidate.items() if k not in ['bindings','budget_policy']}
    b={k:v for k,v in baseline.items() if k!='bindings'}
    replacements=[('original zero-price initial floors; bounded criticality proxy allowance v1 budgets','original zero-price initial floors/budgets'),('initial floor unchanged; bounded criticality proxy allowance v1','initial floor and raw budgets unchanged'),('bounded criticality proxy allowance v1','original budgets retained')]
    for key in ['primary_search_policy','structural_objective','policy']:
        for left,right in replacements:c[key]=c[key].replace(left,right)
    assert c==b
