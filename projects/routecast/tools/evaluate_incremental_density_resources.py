"""Capacity normalized geometry proxy vs same full native channel universe."""
import json
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from prediction_metrics import compare
ROOT=Path(__file__).resolve().parents[1]
start=time.perf_counter()
prior=ROOT/'experiments/incremental_bbox_density_2026-10-07/verification.json'
r=json.loads(prior.read_text());assert all(sha(p)==h for p,h in r['bindings'].items())
protocol=ROOT/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json'
cases=json.loads(protocol.read_text())['cases']
out=ROOT/'experiments/incremental_density_resources_2026-10-07';out.mkdir(exist_ok=False)
bindings={str(prior):sha(prior),str(protocol):sha(protocol),str(Path(__file__)):sha(Path(__file__)),str(ROOT/'tools/prediction_metrics.py'):sha(ROOT/'tools/prediction_metrics.py')}
contexts={};predictions={}
# Complete all predictions before opening any native occupancy labels.
for case in cases:
    w,i=case['width'],case['index']
    ep=json.loads(Path(case['target']).read_text());graph=Path(ep['inputs']['graph']['path'])
    assert sha(graph)==ep['graph_sha256'];bindings[str(graph)]=sha(graph)
    if w not in contexts:
        channels={};capacity=defaultdict(int)
        for _,elem in ET.iterparse(graph,events=('end',)):
            if elem.tag!='node':continue
            if elem.get('type') in ('CHANX','CHANY') and int(elem.get('capacity'))>0:
                loc=elem.find('loc');assert int(loc.get('layer','0'))==0
                d=0 if elem.get('type')=='CHANX' else 1
                cells=[(x,y,d) for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1) for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1)]
                cap=int(elem.get('capacity'));channels[int(elem.get('id'))]=(cap,cells)
                for cell in cells:capacity[cell]+=cap
            elem.clear()
        contexts[w]=(channels,capacity)
    channels,capacity=contexts[w]
    vf=prior.parent/f'w{w}_m{i}.json';assert sha(vf)==r['bindings'][str(vf)]
    bindings[str(vf)]=sha(vf)
    density={tuple(row['cell']):F(row['target']) for row in json.loads(vf.read_text())}
    unsupported=[cell for cell,value in density.items() if value and capacity.get(cell,0)==0]
    predicted={node:sum((density.get(cell,F())/capacity[cell] for cell in cells),F())/len(cells) for node,(_,cells) in channels.items()}
    file=out/f'w{w}_m{i}_prediction.json'
    file.write_text(json.dumps([{'node':node,'utilization_fraction':str(value)} for node,value in sorted(predicted.items())],indent=2)+'\n')
    bindings[str(file)]=sha(file);predictions[w,i]=(predicted,unsupported)
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,definition='Direction cell demand divided by sum of covering same-direction RR capacities, averaged over each RR rectangle; exact Fraction, full positive-capacity channel universe; top20 fixed, ascending ID ties; unsupported cells reported separately',scope='existing development cases; predictions completed before labels, authors previously saw development results; no prospective claim'),indent=2)+'\n')
parent=ROOT/'experiments/mux_full_cohort_cold_lifecycle_2026-10-06'
rp,vp=parent/'receipt.json',parent/'verification.json'
cold=json.loads(rp.read_text());assert json.loads(vp.read_text())['receipt_sha256']==sha(rp)
bindings.update({str(p):sha(p) for p in (rp,vp,out/'protocol.json')});rows=[]
for case in cold['rows']:
    w,i=case['width'],case['index'];assert case['complete'] and case['error'] is None
    sf=parent/f'mux_w{w}_m{i}_0/accepted_state.json'
    assert sha(sf)==case['rounds'][0]['snapshot_sha256'];bindings[str(sf)]=sha(sf)
    state=json.loads(sf.read_text());ledger={int(n):v for n,v in state['ledger'].items()}
    channels,capacity=contexts[w];predicted,unsupported=predictions[w,i]
    truth={node:F(ledger.get(node,0),cap) for node,(cap,_) in channels.items()}
    stats=compare(predicted,truth,20)
    stats={k:(str(v) if isinstance(v,F) else v) for k,v in stats.items()}
    rows.append(dict(width=w,index=i,unsupported_density_cells=len(unsupported),**stats))
assert len(rows)==12 and all(sha(p)==h for p,h in bindings.items())
result=dict(rows=rows,bindings=bindings,outer_seconds=time.perf_counter()-start,scope='12 existing development target placements; full positive-capacity CHANX/CHANY resource universe including zero truth; exact rational ranking. Unnormalized unsupported cells not silently converted to resources. No new native run, heldout/generalization, STA/failure or net gain evidence; outer includes preparation/hash/prediction/evaluation, prepared endpoint+density inputs.')
(out/'evaluation.json').write_text(json.dumps(result,indent=2)+'\n')
print([(x['width'],x['index'],round(x['spearman'],4),x['precision_at_k'],x['unsupported_density_cells']) for x in rows])
print('outer_seconds',result['outer_seconds'])
