"""Recompute final failed-route occupancy as unique net ownership, not edge demand."""
import hashlib,json,re,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments'
B=E/'full_ram_development_route_v1_2026-10-09'
D=E/'full_ram_failed_route_audit_v1_2026-10-09';D.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((B/'receipt.json').read_text());assert r['exit_code']==2
for p,h in {**r['bindings'],**r['files']}.items():assert sha(Path(p))==h
occupancy=Counter(); net_nodes=set();nets=0;seen_nets=set()
def commit():
    occupancy.update(net_nodes)
for line in (B/'design.route').read_text().splitlines():
    match=re.match(r'Net (\d+) ',line)
    if match:
        commit();net_nodes=set();net=int(match[1]);assert net not in seen_nets;seen_nets.add(net);nets+=1
    match=re.match(r'Node:\s+(\d+)\s+',line)
    if match:net_nodes.add(int(match[1]))
commit()
nodes={}
for event,element in ET.iterparse(B/'rr_graph.xml',events=['end']):
    if element.tag=='node' and 'capacity' in element.attrib:
        node=int(element.get('id'));loc=element.find('loc')
        nodes[node]=dict(capacity=int(element.get('capacity')),type=element.get('type'),loc=dict(loc.attrib))
        element.clear()
assert set(occupancy)<=set(nodes)
overused=[dict(node=n,occupancy=occ,**nodes[n]) for n,occ in occupancy.items() if occ>nodes[n]['capacity']]
log=(B/'route.log').read_text()
native=int(re.search(r'Total number of overused nodes: (\d+)',log)[1])
out=dict(native_exit_code=2,nets=nets,unique_used_nodes=len(occupancy),recomputed_overused_nodes=len(overused),native_reported_overused_nodes=native,
    count_matches_native=len(overused)==native,overuse_by_type=dict(Counter(x['type'] for x in overused)),
    total_excess_occupancy=sum(x['occupancy']-x['capacity'] for x in overused),overused=overused,
    termination='Native predicted-success-iteration heuristic abort; not full-graph impossibility proof.',
    scope='Final failed route unique-net occupancy and original XML capacities. Local OPIN reservations not explicitly encoded in route may require separate native parity audit.',
    bindings={str(p):sha(p) for p in [Path(__file__),B/'receipt.json',B/'design.route',B/'rr_graph.xml',B/'route.log']},admitted_for_prediction=False)
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print({k:out[k] for k in ['nets','recomputed_overused_nodes','native_reported_overused_nodes','count_matches_native','overuse_by_type','total_excess_occupancy']})
