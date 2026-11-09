"""Independent XML spatial projection, capacity diagnosis and pairwise metrics."""
import json,math,xml.etree.ElementTree as ET
from collections import defaultdict,Counter
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'full_ram_physical_metric_verification_v1_2026-10-09';D.mkdir(exist_ok=False)
comparison=E/'full_ram_length_geometry_comparison_v1_2026-10-09/comparison.json'
c=json.loads(comparison.read_text())
for p,h in c['bindings'].items():assert sha(p)==h
prediction=E/'full_ram_length_switch_prediction_v1_2026-10-09/prediction.json'
truthfile=E/'full_ram_comb_only_route_audit_v1_2026-10-09/physical_audit.json'
pred=json.loads(prediction.read_text());truth=json.loads(truthfile.read_text())
graph=E/'full_ram_comb_only_route_v1_2026-10-09/rr_graph.xml'
geometry=E/'full_ram_geometry_control_v1_2026-10-09/spatial_prediction.json'
gp=json.loads(geometry.read_text());caps=defaultdict(int);pd=defaultdict(int);td=defaultdict(int)
overflow=[];stack=[]
for event,node in ET.iterparse(graph,events=['start','end']):
    if event=='start':stack.append(node);continue
    parent=stack[-2].tag if len(stack)>1 else None
    if node.tag=='node' and parent=='rr_nodes':
        nid=node.get('id');cap=int(node.get('capacity'));kind=node.get('type')
        pv=pred['node_occupancy'].get(nid,0);tv=truth['node_occupancy'].get(nid,0)
        assert tv<=cap
        if pv>cap:overflow.append(dict(node=int(nid),type=kind,occupancy=pv,capacity=cap))
        if kind in ('CHANX','CHANY') and cap>0:
            loc=node.find('loc');seg=node.find('segment').get('segment_id')
            for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1):
                for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1):
                    key=f'{x},{y},{kind},{seg}';caps[key]+=cap;pd[key]+=pv;td[key]+=tv
        stack[-2].remove(node);node.clear()
    if node.tag=='rr_nodes':break
    stack.pop()
keys=sorted(caps);assert set(keys)==set(gp) and len(keys)==2400
actual=[td[k]/caps[k] for k in keys];physical=[pd[k]/caps[k] for k in keys]
def independent(values):
    rank=lambda xs:[2*sum(v<x for v in xs)+sum(v==x for v in xs)-1 for x in xs]
    a,b=rank(values),rank(actual);center=len(keys)-1
    rho=sum((x-center)*(y-center) for x,y in zip(a,b))/math.sqrt(sum((x-center)**2 for x in a)*sum((y-center)**2 for y in b))
    ps=sorted(range(len(keys)),key=lambda i:(-values[i],keys[i]))[:20]
    ts=sorted(range(len(keys)),key=lambda i:(-actual[i],keys[i]))[:20]
    hits=len(set(ps)&set(ts));mae=math.fsum(abs(x-y) for x,y in zip(values,actual))/len(keys)
    return dict(spearman=rho,top20_hits=hits,mae=mae)
verified={}
for label,values in [('length_switch',physical),('geometry',[gp[k] for k in keys])]:
    result=independent(values);expected=c[label]
    assert abs(result['spearman']-expected['spearman'])<1e-14
    assert result['top20_hits']/20==expected['precision_at_k']==expected['recall_at_k']
    assert abs(result['mae']-expected['mae'])<1e-14
    verified[label]=result
out=dict(passed=True,metrics=verified,overused_prediction_nodes=len(overflow),
    prediction_overuse_by_type=dict(Counter(x['type'] for x in overflow)),
    prediction_excess_occupancy=sum(x['occupancy']-x['capacity'] for x in overflow),
    native_target_overused_nodes=0,overused=overflow,
    bindings={str(p):sha(p) for p in [Path(__file__),comparison,prediction,truthfile,graph,geometry]},
    scope='Independent XML capacity/spatial projection and pairwise metric arithmetic. Physical estimator individual paths overload resources despite strong spatial ranking; not legal routing, calibrated failure prediction or unseen-family/acceleration evidence.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(verified,out['overused_prediction_nodes'],out['prediction_overuse_by_type'],out['prediction_excess_occupancy'])
