"""Same-grid retrospective physical/geometry comparison with all skipped cases."""
import json
import xml.etree.ElementTree as ET
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from prediction_metrics import compare
ROOT=Path(__file__).resolve().parents[1]
physical=ROOT/'experiments/owner50_retained_rr_2026-10-07_predictor'
spatial=ROOT/'experiments/density_spatial_cells_2026-10-07'
rp,vp=physical/'receipt.json',physical/'verification.json'
r,v=json.loads(rp.read_text()),json.loads(vp.read_text());assert v['receipt_sha256']==sha(rp)
ep,mp=spatial/'evaluation.json',spatial/'metric_verification.json'
e=json.loads(ep.read_text());assert json.loads(mp.read_text())['evaluation_sha256']==sha(ep)
assert all(sha(p)==h for p,h in e['bindings'].items())
bindings={str(p):sha(p) for p in (rp,vp,ep,mp,Path(__file__),ROOT/'tools/prediction_metrics.py')}
contexts={};rows=[]
for case in r['rows']:
    w,i=case['width'],case['index'];file=physical/f'w{w}_m{i}/result.json'
    if 'result_sha256' not in case:
        rows.append(dict(width=w,index=i,scored=False,status=case['status'],metrics=None));continue
    assert sha(file)==case['result_sha256'];bindings[str(file)]=sha(file)
    candidate=json.loads(file.read_text())['result']['candidate']
    if candidate is None or candidate['completed_connections']!=candidate['required_connections']:
        rows.append(dict(width=w,index=i,scored=False,status=case['status'],metrics=None));continue
    assert candidate['status'] in ('COMPLETE_CANDIDATE','COMPLETE_DIAGNOSTIC')
    graph=ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128/rr_graph.xml'
    assert sha(graph)==candidate['graph_sha256']==e['bindings'][str(graph)];bindings[str(graph)]=sha(graph)
    if w not in contexts:
        nodes={};caps=defaultdict(int)
        for _,node in ET.iterparse(graph,events=('end',)):
            if node.tag!='node':continue
            if node.get('type') in ('CHANX','CHANY') and int(node.get('capacity'))>0:
                loc=node.find('loc');assert int(loc.get('layer','0'))==0
                direction=0 if node.get('type')=='CHANX' else 1
                cells=[(x,y,direction) for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1) for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1)]
                nodes[int(node.get('id'))]=cells
                for cell in cells:caps[cell]+=int(node.get('capacity'))
            node.clear()
        contexts[w]=nodes,dict(caps)
    nodes,caps=contexts[w]
    predicted_counts=defaultdict(int)
    for node,count in candidate['ledger'].items():
        assert type(count) is int and count>=0
        for cell in nodes.get(int(node),[]):predicted_counts[cell]+=count
    prediction={cell:F(predicted_counts[cell],cap) for cell,cap in caps.items()}
    vector=spatial/f'w{w}_m{i}.json';assert sha(vector)==e['bindings'][str(vector)];bindings[str(vector)]=sha(vector)
    data=json.loads(vector.read_text());assert {tuple(x['cell']):x['capacity'] for x in data}==caps
    truth={tuple(x['cell']):F(x['native']) for x in data}
    geometry={tuple(x['cell']):F(x['prediction']) for x in data}
    pm,gm=compare(prediction,truth,20),compare(geometry,truth,20)
    clean=lambda m:{k:str(value) if isinstance(value,F) else value for k,value in m.items()}
    rows.append(dict(width=w,index=i,scored=True,status=case['status'],candidate_status=candidate['status'],physical=clean(pm),geometry=clean(gm),predictor_loop_seconds=case['loop_seconds'],scope='complete candidate occupancy includes retained old routes and affected repairs; timing rejected candidates still scored, not accepted native route'))
assert len(rows)==12 and all(sha(p)==h for p,h in bindings.items())
out=ROOT/'experiments/physical_geometry_spatial_2026-10-07';out.mkdir(exist_ok=False)
report=dict(bindings=bindings,rows=rows,complete_cases=sum(x['scored'] for x in rows),total_cases=len(rows),scope='Existing development archived predictions vs target cold labels on identical spatial capacity grids. Skips retain null metrics; compare geometry only on same scored subset. Archived preparation/search costs not matched new wall times; no prospective, new physical-path verification/native execution, joint acceptance or netgain.')
(out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print([(x['width'],x['index'],round(x['physical']['spearman'],4),x['physical']['precision_at_k'],x['geometry']['precision_at_k']) if x['scored'] else (x['width'],x['index'],x['status']) for x in rows])
