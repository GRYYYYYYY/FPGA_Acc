"""Full same-direction capacity-cell comparison, separate from resource metrics."""
import json
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from prediction_metrics import compare
ROOT=Path(__file__).resolve().parents[1]
start=time.perf_counter(); prior=ROOT/'experiments/incremental_density_resources_2026-10-07/evaluation.json'
evidence=json.loads(prior.read_text());assert all(sha(p)==h for p,h in evidence['bindings'].items())
out=ROOT/'experiments/density_spatial_cells_2026-10-07';out.mkdir(exist_ok=False)
bindings={str(prior):sha(prior),str(Path(__file__)):sha(Path(__file__)),str(ROOT/'tools/prediction_metrics.py'):sha(ROOT/'tools/prediction_metrics.py')};contexts={};predictions={}
for row in evidence['rows']:
    w,i=row['width'],row['index'];graph=ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128/rr_graph.xml'
    assert sha(graph)==evidence['bindings'][str(graph)];bindings[str(graph)]=sha(graph)
    if w not in contexts:
        covering=defaultdict(list);capacities={}
        for _,node in ET.iterparse(graph,events=('end',)):
            if node.tag!='node':continue
            if node.get('type') in ('CHANX','CHANY') and int(node.get('capacity'))>0:
                loc=node.find('loc');assert int(loc.get('layer','0'))==0
                nid=int(node.get('id'));capacities[nid]=int(node.get('capacity'));d=0 if node.get('type')=='CHANX' else 1
                for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1):
                    for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1):covering[x,y,d].append(nid)
            node.clear()
        cellcaps={cell:sum(capacities[n] for n in nodes) for cell,nodes in covering.items()}
        contexts[w]=covering,cellcaps
    vf=ROOT/f'experiments/incremental_bbox_density_2026-10-07/w{w}_m{i}.json'
    assert sha(vf)==evidence['bindings'][str(vf)];bindings[str(vf)]=sha(vf)
    density={tuple(r['cell']):F(r['target']) for r in json.loads(vf.read_text())}
    covering,caps=contexts[w];pred={cell:density.get(cell,F())/cap for cell,cap in caps.items()}
    predictions[w,i]=pred
# No native labels before all spatial predictions are complete.
rows=[]
for row in evidence['rows']:
    w,i=row['width'],row['index'];sf=ROOT/f'experiments/mux_full_cohort_cold_lifecycle_2026-10-06/mux_w{w}_m{i}_0/accepted_state.json'
    assert sha(sf)==evidence['bindings'][str(sf)];bindings[str(sf)]=sha(sf)
    ledger={int(n):v for n,v in json.loads(sf.read_text())['ledger'].items()}
    covering,caps=contexts[w];pred=predictions[w,i]
    truth={cell:F(sum(ledger.get(n,0) for n in nodes),caps[cell]) for cell,nodes in covering.items()}
    stats=compare(pred,truth,20)
    stats={k:str(v) if isinstance(v,F) else v for k,v in stats.items()}
    vector=out/f'w{w}_m{i}.json'
    vector.write_text(json.dumps([dict(cell=cell,capacity=caps[cell],prediction=str(pred[cell]),native=str(truth[cell])) for cell in sorted(caps)],indent=2)+'\n')
    bindings[str(vector)]=sha(vector)
    rows.append(dict(width=w,index=i,**stats))
assert all(sha(p)==h for p,h in bindings.items())
result=dict(rows=rows,bindings=bindings,outer_seconds=time.perf_counter()-start,scope='12 existing development moves, full positive-capacity direction-cell universe including zeros. Native occupancy/capacity sums every covering physical RR node; bbox demand uses original cell values, not average reconstructed node scores. Fixed k20, lexicographic cell tie rule. Spatial and resource metrics distinct, no replacement of resource failure. No new native, heldout, route/STA or netgain.')
(out/'evaluation.json').write_text(json.dumps(result,indent=2)+'\n')
print([(r['width'],r['index'],round(r['spearman'],4),r['precision_at_k'],r['universe_size']) for r in rows])
