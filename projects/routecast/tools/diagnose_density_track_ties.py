"""Retrospective tie sensitivity without changing predictor or primary top20."""
import json
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'experiments/incremental_density_resources_2026-10-07'
ep=base/'evaluation.json';ev=json.loads(ep.read_text())
assert all(sha(p)==h for p,h in ev['bindings'].items())
rows=[];bindings={str(ep):sha(ep),str(Path(__file__)):sha(Path(__file__))}
for x in ev['rows']:
    w,i=x['width'],x['index'];pf=base/f'w{w}_m{i}_prediction.json'
    sf=ROOT/f'experiments/mux_full_cohort_cold_lifecycle_2026-10-06/mux_w{w}_m{i}_0/accepted_state.json'
    assert sha(pf)==ev['bindings'][str(pf)] and sha(sf)==ev['bindings'][str(sf)]
    bindings.update({str(p):sha(p) for p in (pf,sf)})
    predicted={v['node']:F(v['utilization_fraction']) for v in json.loads(pf.read_text())}
    ledger={int(n):v for n,v in json.loads(sf.read_text())['ledger'].items()}
    # All channels in this architecture are unit capacity; verify from graph.
    import xml.etree.ElementTree as ET
    graph=ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128/rr_graph.xml'
    caps={}
    for _,node in ET.iterparse(graph,events=('end',)):
        if node.tag=='node':
            if node.get('type') in ('CHANX','CHANY') and int(node.get('capacity'))>0:caps[int(node.get('id'))]=int(node.get('capacity'))
            node.clear()
    assert predicted.keys()==caps.keys()
    truth={n:F(ledger.get(n,0),caps[n]) for n in caps}
    top=sorted(predicted,key=lambda n:(-predicted[n],n))[:20]
    native=sorted(truth,key=lambda n:(-truth[n],n))[:20]
    assert len(set(top)&set(native))/20==x['precision_at_k']
    boundary=predicted[top[-1]]
    tied={n for n in predicted if predicted[n]==boundary}
    mandatory={n for n in predicted if predicted[n]>boundary}
    slots=20-len(mandatory)
    hit_mandatory=len(mandatory&set(native));hits_tied=len(tied&set(native))
    minimum=hit_mandatory+max(0,slots-(len(tied)-hits_tied))
    maximum=hit_mandatory+min(slots,hits_tied)
    rows.append(dict(width=w,index=i,prediction_boundary_ties=len(tied),native_boundary_ties=sum(v==truth[native[-1]] for v in truth.values()),fixed_rule_hits=len(set(top)&set(native)),minimum_hits_over_prediction_boundary_ties=minimum,maximum_hits_over_prediction_boundary_ties=maximum,positive_native_occupancy_in_predicted_top20=sum(truth[n]>0 for n in top)))
report=dict(bindings=bindings,rows=rows,scope='Primary ascending-ID top20 unchanged; min/max vary ONLY prediction boundary ties against fixed native top20. Native ties reported, not jointly optimized. Does not repair ranking, establish spatial hotspot accuracy, or new prospective metrics.')
(base/'tie_diagnosis.json').write_text(json.dumps(report,indent=2)+'\n')
print(rows)
