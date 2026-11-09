"""Trace frozen native/model hotspot supports and named NET owners."""
import json,sys,xml.etree.ElementTree as E
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from audit_native_route import NET,NODE
base=R/'experiments/ethernet_hotspots_v1_2026-10-08'
proof=base/'metric_verification.json';p=json.loads(proof.read_text())
assert p['histogram_ranks_topk_mae_and_full_vector_scope_pass'] and all(sha(k)==v for k,v in p['bindings'].items())
bindings=closure([Path(__file__)])
def load(path):
    bindings[str(path)]=sha(path);return json.loads(path.read_text())
bindings[str(proof)]=sha(proof)
v=load(base/'comparison_vectors.json');bins=v['bins']
tops={m:sorted(bins,key=lambda x:(-(x['native'] if m=='native' else x['predictions'][m])/x['capacity'],tuple(x['key'])))[:20] for m in ['native','wire_shared']}
targets={tuple(x['key']):x for rows in tops.values() for x in rows}
ep=load(R/'experiments/ethernet_native_demand_v1_2026-10-08/endpoints.json')
s=load(R/'experiments/ethernet_resident_v1_2026-10-08/resident/sketch.json')
graph=Path(ep['inputs']['graph']['path']);bindings[str(graph)]=sha(graph);assert sha(graph)==ep['graph_sha256']
supports={k:set() for k in targets};capacities={};stack=[];edge_id=0
required_edges={e for r in s['records'] for e in r['answer']['physical_edge_ids']}
selected_edges={}
for event,el in E.iterparse(graph,events=('start','end')):
    if event=='start':stack.append(el);continue
    if el.tag=='node' and el.get('type') in {'CHANX','CHANY'} and int(el.get('capacity'))>0:
        loc=el.find('loc').attrib;seg=el.find('segment');sid=int(seg.get('segment_id')) if seg is not None else -1;n=int(el.get('id'))
        for k in targets:
            if (int(loc.get('layer','0')),el.get('type'),sid)==(k[0],k[3],k[4]) and int(loc['xlow'])<=k[1]<=int(loc['xhigh']) and int(loc['ylow'])<=k[2]<=int(loc['yhigh']):
                supports[k].add(n);capacities[n]=int(el.get('capacity'))
    elif el.tag=='edge':
        if edge_id in required_edges:selected_edges[edge_id]=(int(el.get('src_node')),int(el.get('sink_node')))
        edge_id+=1
    if el.tag in {'node','edge'}:
        if len(stack)>1:stack[-2].remove(el)
        el.clear()
    stack.pop()
assert len(selected_edges)==len(required_edges)
selected=set(capacities);model=defaultdict(set);independent=defaultdict(int)
for r in s['records']:
    nodes={n for e in r['answer']['physical_edge_ids'] for n in selected_edges[e]}&selected
    for n in nodes:model[n].add(ep['net_names'][str(r['net_id'])]);independent[n]+=1
native=defaultdict(set);route=R/'experiments/ethernet_native_cold_v1_2026-10-08/output.route';bindings[str(route)]=sha(route);name=None
for line in route.read_text().splitlines():
    if m:=NET.match(line):name=m[2]
    elif m:=NODE.match(line):
        n=int(m[1])
        if n in selected:assert name is not None;native[n].add(name)
rows=[]
for k,nodes in sorted(supports.items()):
    x=targets[k]
    assert sum(capacities[n] for n in nodes)==x['capacity']
    assert sum(len(native[n]) for n in nodes)==x['native']
    assert sum(len(model[n]) for n in nodes)==x['predictions']['wire_shared']
    assert sum(independent[n] for n in nodes)==x['predictions']['wire_independent']
    nu=set().union(*(native[n] for n in nodes));mu=set().union(*(model[n] for n in nodes))
    rows.append(dict(key=list(k),capacity=x['capacity'],physical_nodes=sorted(nodes),native_demand=x['native'],model_demand=x['predictions']['wire_shared'],native_NETs=sorted(nu),model_NETs=sorted(mu),common_NETs=sorted(nu&mu),missing_NETs=sorted(nu-mu),extra_NETs=sorted(mu-nu),node_owners=[dict(node=n,native=sorted(native[n]),model=sorted(model[n])) for n in sorted(nodes)]))
out=R/'experiments/ethernet_hotspot_owners_v1_2026-10-08';out.mkdir()
assert all(sha(k)==v for k,v in bindings.items())
(out/'diagnosis.json').write_text(json.dumps(dict(bindings=bindings,bins=rows,selected_nodes=len(selected),unique_physical_supports=len({tuple(sorted(n)) for n in supports.values()}),all_selected_original_XML_support_capacity_and_both_named_NET_demands_pass=True,scope='Post-hoc frozen native/final top20 union only; direct original XML edges plus text route named NET sets. Different NETs at a bin are path-choice differences, not omitted full queries. No causality/optimality or generalized prediction success.'),indent=2)+'\n')
print('PASS hotspot owners',len(rows),len(selected),flush=True)
