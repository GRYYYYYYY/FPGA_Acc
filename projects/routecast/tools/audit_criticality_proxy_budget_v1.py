"""Independent Fraction ceiling oracle; never imports producer budget implementation."""
import json,math,struct
from fractions import Fraction
POLICY='original_budget_plus_ceil_one_minus_criticality_times_floor_v1'
def expected(floor,scale,c):
    assert type(floor) is int and floor>=0 and type(scale) is int and scale>0 and isinstance(c,Fraction) and 0<=c<=1
    original=max(scale//10**9,(3*floor+1)//2)
    return original+math.ceil((1-c)*floor)
def criticalities(proof,queries,sha):
    from pathlib import Path
    proof=Path(proof);v=json.loads(proof.read_text());assert v['nonignored_pin_keys_exactly_manifest'] and all(sha(p)==h for p,h in v['bindings'].items())
    values={};keys=set();globalpins=set()
    for row in json.loads((proof.parent/'initial_connection_criticalities.json').read_text()):
        cid=row['connection_id'];q=queries[cid];key=(row['net'],row['local_sink_pin']);assert cid not in values and key not in keys and row['global_pin'] not in globalpins
        assert (row['net'],row['source_rr'],row['target_rr'])==(q['net_id'],q['source'],q['sink'])
        c=Fraction(struct.unpack('<f',struct.pack('<f',float(row['criticality_float32_text'])))[0]);assert 0<=c<=1
        values[cid]=c;keys.add(key);globalpins.add(row['global_pin'])
    assert set(values)==set(queries)
    return values
