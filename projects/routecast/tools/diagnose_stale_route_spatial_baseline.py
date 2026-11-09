"""Separate old-route prior from incremental candidate occupancy contribution."""
import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
from prediction_metrics import compare
ROOT=Path(__file__).resolve().parents[1]
cp=ROOT/'experiments/physical_geometry_spatial_2026-10-07/comparison.json'
c=json.loads(cp.read_text());assert all(sha(p)==h for p,h in c['bindings'].items())
op=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/receipt.json';old=json.loads(op.read_text())
bindings={str(p):sha(p) for p in (cp,op,Path(__file__),ROOT/'tools/native_route_ledger_import_compact.py',ROOT/'tools/prediction_metrics.py')}
for row in old['rows']:
    assert row['exit_code']==0 and row['mismatches']==row['fixups']==0
    for path,digest in row['files'].items():assert sha(path)==digest;bindings[path]=digest
contexts={};rows=[]
def occupancy(path):
    paths=physical_paths(path)
    return Counter(node for branches in paths.values() for node in {n for branch in branches for n,_ in branch})
def clean(m):return {k:str(v) if isinstance(v,F) else v for k,v in m.items()}
for case in c['rows']:
    w,i=case['width'],case['index']
    if not case['scored']:
        rows.append(dict(width=w,index=i,scored=False,status=case['status'],metrics=None));continue
    if w not in contexts:
        original=ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128/design.route'
        canonical=ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}/canonical/design.route'
        assert str(canonical) in bindings
        oldledger=occupancy(original);assert oldledger==occupancy(canonical)
        bindings[str(original)]=sha(original)
        graph=original.parent/'rr_graph.xml';assert sha(graph)==c['bindings'][str(graph)];bindings[str(graph)]=sha(graph)
        nodes={}
        for _,node in ET.iterparse(graph,events=('end',)):
            if node.tag!='node':continue
            if node.get('type') in ('CHANX','CHANY') and int(node.get('capacity'))>0:
                loc=node.find('loc');d=0 if node.get('type')=='CHANX' else 1
                nodes[int(node.get('id'))]=[(x,y,d) for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1) for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1)]
            node.clear()
        contexts[w]=nodes,oldledger
    nodes,oldledger=contexts[w]
    vf=ROOT/f'experiments/density_spatial_cells_2026-10-07/w{w}_m{i}.json'
    assert sha(vf)==c['bindings'][str(vf)];bindings[str(vf)]=sha(vf)
    data=json.loads(vf.read_text());caps={tuple(x['cell']):x['capacity'] for x in data}
    truth={tuple(x['cell']):F(x['native']) for x in data}
    result=ROOT/f'experiments/owner50_retained_rr_2026-10-07_predictor/w{w}_m{i}/result.json'
    assert sha(result)==c['bindings'][str(result)];bindings[str(result)]=sha(result)
    candidate=json.loads(result.read_text())['result']['candidate']
    def project(ledger):
        counts=defaultdict(int)
        for node,count in ledger.items():
            for cell in nodes.get(int(node),[]):counts[cell]+=count
        return {cell:F(counts[cell],cap) for cell,cap in caps.items()}
    stale=project(oldledger);prediction=project(candidate['ledger'])
    sm,pm=compare(stale,truth,20),compare(prediction,truth,20)
    assert clean(pm)==case['physical']
    actual_delta={cell:truth[cell]-stale[cell] for cell in caps}
    predicted_delta={cell:prediction[cell]-stale[cell] for cell in caps}
    changed={cell for cell in caps if actual_delta[cell]!=0}
    # All-domain MAE of deltas equals occupancy MAE algebraically; changed-only exposes dilution.
    selected_error=lambda pred:sum(abs(pred[cell]-actual_delta[cell]) for cell in changed)/len(changed) if changed else None
    pred_error=selected_error(predicted_delta);zero_error=selected_error(dict.fromkeys(caps,F()))
    rows.append(dict(width=w,index=i,scored=True,candidate_status=candidate['status'],stale=clean(sm),physical=clean(pm),native_changed_cells=len(changed),predicted_changed_cells=sum(bool(x) for x in predicted_delta.values()),changed_only_delta_mae_candidate=str(pred_error) if pred_error is not None else None,changed_only_delta_mae_zero_baseline=str(zero_error) if zero_error is not None else None,all_cell_mae_improved=pm['mae']<sm['mae'],changed_only_delta_mae_improved=pred_error<zero_error if changed else None,top20_hits_change=round((pm['precision_at_k']-sm['precision_at_k'])*20)))
assert all(sha(p)==h for p,h in bindings.items())
out=ROOT/'experiments/stale_route_spatial_baseline_2026-10-07';out.mkdir(exist_ok=False)
report=dict(bindings=bindings,rows=rows,scope='Retrospective 8 scored +4 explicit skipped development moves. Stale old-route occupancy is predictor-only baseline, not a legal new-target route. Original/canonical old NET-union occupancy parity verified. Native-changed-only mask uses labels for evaluation only, not selection. No heldout/native execution/full-cost gain.')
(out/'diagnosis.json').write_text(json.dumps(report,indent=2)+'\n')
print([(x['width'],x['index'],round(x['stale']['spearman'],4),round(x['physical']['spearman'],4),x['top20_hits_change'],x['all_cell_mae_improved'],x['changed_only_delta_mae_improved']) for x in rows if x['scored']])
