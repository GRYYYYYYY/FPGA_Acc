"""Freeze observable masks without target route labels, then evaluate leakage."""
import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[1]
prior=ROOT/'experiments/stale_route_spatial_baseline_2026-10-07/diagnosis.json'
evidence=json.loads(prior.read_text());assert all(sha(p)==h for p,h in evidence['bindings'].items())
protocol=ROOT/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json'
cases=json.loads(protocol.read_text())['cases']
out=ROOT/'experiments/observable_affected_cells_2026-10-07';out.mkdir(exist_ok=False)
bindings={str(p):sha(p) for p in (prior,protocol,Path(__file__),ROOT/'tools/native_route_ledger_import_compact.py')}
contexts={};prepared={}
for case in cases:
    w,i=case['width'],case['index'];oldfile,targetfile=Path(case['old']),Path(case['target'])
    old,target=[json.loads(p.read_text()) for p in (oldfile,targetfile)]
    for p in (oldfile,targetfile):assert sha(p)==case['inputs'][str(p)];bindings[str(p)]=sha(p)
    graph=Path(old['inputs']['graph']['path']);assert sha(graph)==old['graph_sha256']==target['graph_sha256'];bindings[str(graph)]=sha(graph)
    if w not in contexts:
        nodecells={};locations={};caps=defaultdict(int)
        for _,node in ET.iterparse(graph,events=('end',)):
            if node.tag!='node':continue
            loc=node.find('loc');assert int(loc.get('layer','0'))==0
            nid=int(node.get('id'));locations[nid]=(int(loc.get('xlow')),int(loc.get('ylow')))
            if node.get('type') in ('CHANX','CHANY') and int(node.get('capacity'))>0:
                direction=0 if node.get('type')=='CHANX' else 1
                cells={(x,y,direction) for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1) for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1)}
                nodecells[nid]=cells
                for cell in cells:caps[cell]+=int(node.get('capacity'))
            node.clear()
        route=ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128/design.route'
        assert sha(route)==evidence['bindings'][str(route)];bindings[str(route)]=sha(route)
        paths=physical_paths(route)
        byname={name:{n for path in branches for n,_ in path} for name,branches in paths.items()}
        oldledger=Counter(n for nodes in byname.values() for n in nodes)
        contexts[w]=nodecells,locations,dict(caps),byname,oldledger
    nodecells,locations,caps,byname,oldledger=contexts[w]
    original={r['connection_id']:r for r in old['connections']};changed=[r for r in target['connections'] if (r['source'],r['sink'])!=(original[r['connection_id']]['source'],original[r['connection_id']]['sink'])]
    dirty={r['net_id'] for r in changed};mask=set()
    for net in dirty:
        name=old['net_names'][str(net)];assert target['net_names'][str(net)]==name and name in byname
        for node in byname[name]:mask.update(nodecells.get(node,set()))
        # Include complete old and target NET boxes in both directions, no halo tuning.
        for endpoints in (old,target):
            nodes={r[k] for r in endpoints['connections'] if r['net_id']==net for k in ('source','sink')}
            points=[locations[n] for n in nodes]
            for x in range(min(p[0] for p in points),max(p[0] for p in points)+1):
                for y in range(min(p[1] for p in points),max(p[1] for p in points)+1):
                    mask.update(((x,y,0),(x,y,1)))
    mask.intersection_update(caps)
    mf=out/f'w{w}_m{i}_mask.json';mf.write_text(json.dumps(sorted(mask))+'\n');bindings[str(mf)]=sha(mf)
    prepared[w,i]=mask,dirty
# All 12 masks persisted BEFORE reading target native occupancy/quality labels.
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,definition='Union of old physical channel footprints and full old/target endpoint boxes for endpoint-changed NETs, both directions; intersect complete positive-capacity grid; no fitted halo or native target information',scope='Development retrospective, fixed mask; authors know earlier labels; not prospective'),indent=2)+'\n')
bindings[str(out/'protocol.json')]=sha(out/'protocol.json');rows=[]
for case in cases:
    w,i=case['width'],case['index'];mask,dirty=prepared[w,i];nodecells,locations,caps,byname,oldledger=contexts[w]
    vector=ROOT/f'experiments/density_spatial_cells_2026-10-07/w{w}_m{i}.json'
    spatial=ROOT/'experiments/density_spatial_cells_2026-10-07/evaluation.json'
    expected=json.loads(spatial.read_text())['bindings'];assert sha(vector)==expected[str(vector)];bindings[str(vector)]=sha(vector);bindings[str(spatial)]=sha(spatial)
    data=json.loads(vector.read_text());assert {tuple(x['cell']):x['capacity'] for x in data}==caps
    truth={tuple(x['cell']):F(x['native']) for x in data}
    def project(ledger):
        counts=defaultdict(int)
        for n,count in ledger.items():
            for cell in nodecells.get(int(n),set()):counts[cell]+=count
        return {cell:F(counts[cell],cap) for cell,cap in caps.items()}
    stale=project(oldledger);delta={cell:truth[cell]-stale[cell] for cell in caps};actual={cell for cell,value in delta.items() if value}
    inside=actual&mask;outside=actual-mask
    mass=sum(abs(value) for value in delta.values());captured=sum(abs(delta[cell]) for cell in mask)
    row=dict(width=w,index=i,dirty_nets=len(dirty),mask_cells=len(mask),universe_cells=len(caps),actual_changed_cells=len(actual),outside_changed_cells=len(outside),change_cell_recall=str(F(len(inside),len(actual))) if actual else None,change_mass_recall=str(captured/mass) if mass else None,mask_fraction=str(F(len(mask),len(caps))))
    file=ROOT/f'experiments/owner50_retained_rr_2026-10-07_predictor/w{w}_m{i}/result.json'
    if str(file) in evidence['bindings']:
        assert sha(file)==evidence['bindings'][str(file)];bindings[str(file)]=sha(file)
        candidate=json.loads(file.read_text())['result']['candidate'];prediction=project(candidate['ledger'])
        def error(values,cells):return sum(abs(values[cell]-truth[cell]) for cell in cells)/len(cells) if cells else None
        ce,se=error(prediction,mask),error(stale,mask)
        row.update(candidate_mask_mae=str(ce) if ce is not None else None,stale_mask_mae=str(se) if se is not None else None,candidate_mask_improved=ce<se if ce is not None else None)
    else:row.update(candidate_mask_mae=None,stale_mask_mae=None,candidate_mask_improved=None,status='PRIOR_ALLOCATION_SKIP')
    rows.append(row)
assert all(sha(p)==h for p,h in bindings.items())
(out/'evaluation.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,scope='All12 observable masks; 8 candidate/4 skip. Target native changes used only AFTER masks frozen for evaluation. Mask not a safe locality bound: outside changes retained. No heldout, new native, legal route, STA or netgain.'),indent=2)+'\n')
print([(x['width'],x['index'],x['mask_cells'],x['universe_cells'],x['outside_changed_cells'],x['candidate_mask_improved']) for x in rows])
