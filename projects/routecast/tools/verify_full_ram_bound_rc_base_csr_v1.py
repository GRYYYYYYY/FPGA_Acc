"""Independently validate every prepared arc/cost against original XML."""
import json,xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from prepared_csr import read,U64
R=Path(__file__).resolve().parents[1];E=R/'experiments'
B=E/'full_ram_bound_rc_base_prediction_v1_2026-10-09'
D=E/'full_ram_bound_rc_base_csr_verification_v1_2026-10-09';D.mkdir(exist_ok=False)
graph=E/'full_ram_comb_only_route_v1_2026-10-09/rr_graph.xml'
m,f=read(B/'csr',sha(graph));ids=f['node_ids'];rank={n:i for i,n in enumerate(ids)}
costs={};topology={}
for row,n in enumerate(ids):
    for slot in range(f['row_offsets'][row],f['row_offsets'][row+1]):
        eid=f['edge_ids'][slot];topology[eid]=(n,ids[f['dest_ranks'][slot]],f['switch_ids'][slot]);costs[eid]=f['costs'][slot]
import csv
N=E/'full_ram_native_node_binding_v1_2026-10-09'
proof=E/'full_ram_native_node_binding_verification_v1_2026-10-09/verification.json'
v=json.loads(proof.read_text());assert v['passed']
for p,h in v['bindings'].items():assert sha(p)==h
text=(N/'rr_indexed_data.echo').read_text().splitlines();norm=Fraction(text[0].split(':',1)[1].strip())
base={int(line.split()[0]):Fraction(line.split()[-7]) for line in text[2:] if line.strip()}
index={int(row['node_id']):int(row['cost_index']) for row in csv.DictReader((N/'routecast_node_cost_indices.csv').open())}
def nearest_even(x):
 q,r=divmod(x.numerator,x.denominator)
 return q+int(2*r>x.denominator or (2*r==x.denominator and q%2))
nodes={};delays={};edge=0;disabled=0;stack=[]
for event,x in ET.iterparse(graph,events=['start','end']):
    if event=='start':stack.append(x);continue
    parent=stack[-2].tag if len(stack)>1 else None
    if x.tag=='switch' and parent=='switches':
        assert x.get('type') in ('mux','buffer','tristate')
        timing=x.find('timing');assert timing is not None
        delays[int(x.get('id'))]=tuple(Fraction(timing.get(k,'0')) for k in ('R','Tdel','Cinternal'))
    if x.tag=='node' and parent=='rr_nodes':
        n=int(x.get('id'));cap=int(x.get('capacity'));loc=x.find('loc')
        length=max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))+1 if x.get('type') in ('CHANX','CHANY') else 0
        timing=x.find('timing');assert timing is not None
        nodes[n]=(cap,Fraction(timing.get('R')),Fraction(timing.get('C')));assert f['capacities'][rank[n]]==cap
    if x.tag=='edge' and parent=='rr_edges':
        src,dst,switch=(int(x.get(k)) for k in ('src_node','sink_node','switch_id'))
        assert topology[edge]==(src,dst,switch)
        sr,td,ci=delays[switch];_,r,c=nodes[dst]
        increment=td+(sr+r/2)*c+(sr+r-nodes[src][1]/2)*ci
        assert increment>=0
        expected=nearest_even((increment+base[index[dst]])*10**6/(2*norm)) if nodes[dst][0]>0 else U64
        assert costs[edge]==expected
        disabled+=expected==U64;edge+=1
    if (x.tag,parent) in [('switch','switches'),('node','rr_nodes'),('edge','rr_edges')]:stack[-2].remove(x);x.clear()
    stack.pop()
assert len(nodes)==m['nodes'] and edge==m['edges']
out=dict(passed=True,nodes=len(nodes),edges_checked=edge,disabled_arcs=disabled,
    bindings={str(p):sha(p) for p in [Path(__file__),graph,B/'protocol.json',B/'csr/manifest.json',proof,N/'rr_indexed_data.echo',N/'routecast_node_cost_indices.csv']},
    scope='Independent original XML arc identity/capacity and independent exact Fraction buffered RC and native base equal-half costs with manually implemented ties-even rounding; no RC/timing calibration, shortest-path optimality or target-label use.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(out['nodes'],edge,'all CSR costs match XML')
