"""Compare physical owner-shard inventory to canonical electrical usage."""
import csv, struct
from collections import Counter

def verify_owner_usage(route,nodes,partitioned,repeats):
    def rows(name):
        with (route/name).open() as stream:
            return [{k:int(v) for k,v in r.items()} for r in csv.DictReader(stream)]
    canonical=rows('usage.csv');inventory=rows('owner_usage.csv')
    expected=Counter(tuple(sorted(r.items())) for r in canonical)
    actual=Counter();owners={};records=Counter();boundary=Counter()
    for r in inventory:
        assert set(r)=={'repeat','owner','node','net','history','version'}
        rep,n,die=r['repeat'],r['node'],r['owner'];assert 0<=rep<repeats and 0<=n<len(nodes)//64
        mask=struct.unpack_from('<I',nodes,64*n+20)[0];assert 0<mask<256
        assert die==((mask&-mask).bit_length()-1 if partitioned else 0),'wrong authoritative owner'
        key=(rep,n);assert key not in owners or owners[key]==die,'duplicated electrical authority'
        if key not in owners:
            records[(rep,die)]+=1;boundary[(rep,die)]+=bool(mask&(mask-1))
        owners[key]=die
        actual[tuple(sorted((k,v) for k,v in r.items() if k!='owner'))]+=1
    assert actual==expected,'owner shards differ from canonical usage/tombstones'
    assert all(v==1 for v in actual.values()),'duplicate owner inventory row'
    assert inventory==sorted(inventory,key=lambda r:(r['repeat'],r['owner'],r['node'],r['net'])),'noncanonical shard inventory'
    return dict(unique_owner_inventory_verified=True,partitioned=bool(partitioned),
                records=[dict(repeat=rep,owner=die,records=count,boundary_records=boundary[(rep,die)]) for (rep,die),count in sorted(records.items())],
                scope='Final shard inventory including empty version/history tombstones; no concurrency or HBM claim')
