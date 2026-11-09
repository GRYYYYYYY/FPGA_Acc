import json
import random
from pathlib import Path
from packed_physical_edge_slots_v1 import EdgeSlots
from pre_route_endpoints import sha

def main():
    out=Path(__file__).resolve().parents[1]/'experiments/packed_physical_edge_slots_contract_v1_2026-10-13';out.mkdir(exist_ok=False)
    entries=0
    for n in (0,1,2,17,4096):
        for seed in range(20):
            ids=list(range(n))
            if seed:random.Random(seed).shuffle(ids)
            expected={eid:slot for slot,eid in enumerate(ids)};actual=EdgeSlots(ids)
            assert dict(actual)==expected and len(actual)==n
            ids[:]=[];assert dict(actual)==expected
            for bad in (-1,n,None,1.1,True):
                try:actual[bad]
                except KeyError:pass
                else:raise AssertionError('invalid physical ID accepted')
            if actual.inverse is not None:
                try:actual.inverse[0]=9
                except TypeError:pass
                else:raise AssertionError('mutable inverse')
            entries+=n
    for ids in ([0,0],[1],[0,3],[0,1.0],[-1,0],[0,True]):
        try:EdgeSlots(ids)
        except ValueError:pass
        else:raise AssertionError('invalid permutation accepted')
    sources=[Path(__file__),Path(__file__).with_name('packed_physical_edge_slots_v1.py')]
    result=dict(bindings={str(p.resolve()):sha(p) for p in sources},all_pass=True,permutations=100,entries_compared=entries,
                scope='Complete inverse equality, detached immutable storage and invalid identity rejection. Full model event equivalence required separately.')
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PACKED EDGE SLOT CONTRACT PASS',entries)

if __name__=='__main__':main()
