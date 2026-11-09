"""Independent full rational spatial reconstruction on actual moves."""
import json
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from incremental_bbox_density import DensityState
ROOT=Path(__file__).resolve().parents[1]

def full(rows, locations):
    groups=defaultdict(set)
    for row in rows: groups[row['net_id']].update((row['source'],row['sink']))
    result=defaultdict(F)
    for nodes in groups.values():
        xs=[locations[n][0] for n in nodes];ys=[locations[n][1] for n in nodes]
        lo,hi,b,t=min(xs),max(xs),min(ys),max(ys)
        for x in range(lo,hi+1):
            for y in range(b,t+1):
                for d,length in enumerate((hi-lo,t-b)):
                    if length: result[x,y,d]+=F(length,(hi-lo+1)*(t-b+1))
    return dict(result)

def run():
    begin=time.perf_counter(); prior=ROOT/'experiments/incremental_net_geometry_2026-10-07/verification.json'
    evidence=json.loads(prior.read_text())
    protocol=ROOT/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json'
    bindings={str(prior):sha(prior),str(protocol):sha(protocol)}
    for path,digest in evidence['bindings'].items():assert sha(path)==digest
    out=ROOT/'experiments/incremental_bbox_density_2026-10-07';out.mkdir(exist_ok=False)
    rows=[];cache={}
    for case in json.loads(protocol.read_text())['cases']:
        oldfile,targetfile=Path(case['old']),Path(case['target'])
        old,target=[json.loads(p.read_text()) for p in (oldfile,targetfile)]
        for path in (oldfile,targetfile):bindings[str(path)]=sha(path)
        graph=Path(old['inputs']['graph']['path'])
        assert old['graph_sha256']==target['graph_sha256']==sha(graph)
        bindings[str(graph)]=sha(graph)
        if str(graph) not in cache:
            locations={}
            for _,elem in ET.iterparse(graph,events=('end',)):
                if elem.tag=='node':
                    loc=elem.find('loc');assert int(loc.get('layer','0'))==0
                    locations[int(elem.get('id'))]=(int(loc.get('xlow')),int(loc.get('ylow')));elem.clear()
            cache[str(graph)]=locations
        locations=cache[str(graph)]
        t=time.perf_counter();state=DensityState(old['connections'],locations);setup=time.perf_counter()-t
        assert state.demand==full(old['connections'],locations)
        oldrows={r['connection_id']:r for r in old['connections']}
        assert {r['connection_id'] for r in target['connections']}==oldrows.keys()
        changes=[r for r in target['connections'] if r!=oldrows[r['connection_id']]]
        seed=dict(state.demand);t=time.perf_counter();stats=state.update(changes,0);update=time.perf_counter()-t
        t=time.perf_counter();expected=full(target['connections'],locations);rebuild=time.perf_counter()-t
        assert state.demand==expected
        # Sum of directional density over all cells must equal aggregate HPWL.
        assert sum(state.demand.values())==state.geometry.total
        snapshot=(dict(state.demand),dict(state.geometry.rows),state.geometry.epoch)
        for bad,epoch in ((changes,0),([dict(target['connections'][0],sink=max(locations)+1)],1),([target['connections'][0]]*2,1)):
            try:state.update(bad,epoch)
            except (KeyError,ValueError):pass
            else:raise AssertionError('invalid transaction accepted')
            assert snapshot==(dict(state.demand),dict(state.geometry.rows),state.geometry.epoch)
        reverse=[oldrows[r['connection_id']] for r in changes]
        state.update(reverse,1);assert state.demand==seed
        cells=sorted(set(seed)|set(expected))
        vector=out/f"w{case['width']}_m{case['index']}.json"
        vector.write_text(json.dumps([{'cell':cell,'old':str(seed.get(cell,F())),'target':str(expected.get(cell,F()))} for cell in cells],indent=2)+'\n')
        bindings[str(vector)]=sha(vector)
        rows.append(dict(width=case['width'],index=case['index'],**stats,seed_setup_seconds=setup,incremental_update_seconds=update,full_rebuild_seconds=rebuild,old_peak=str(max(seed.values(),default=F())),target_peak=str(max(expected.values(),default=F())),parity=True,reverse_restores_seed=True,invalid_updates_atomic=True))
    for path in (Path(__file__),ROOT/'tools/incremental_bbox_density.py',ROOT/'tools/incremental_net_geometry.py'):bindings[str(path)]=sha(path)
    assert all(sha(p)==h for p,h in bindings.items())
    report=dict(rows=rows,bindings=bindings,outer_seconds=time.perf_counter()-begin,scope='12 existing development moves; exact Fraction bbox directional density, no RR capacity normalization/physical route/STA or admissions. Prepared endpoints; graph parsing/hash and independent proofs included outer. No native labels read, no net time gain claim.')
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(cases=len(rows),outer_seconds=report['outer_seconds'],update_seconds=sum(r['incremental_update_seconds'] for r in rows),full_rebuild_seconds=sum(r['full_rebuild_seconds'] for r in rows))))
if __name__=='__main__':run()
