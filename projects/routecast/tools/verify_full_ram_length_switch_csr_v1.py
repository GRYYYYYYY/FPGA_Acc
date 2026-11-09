"""Independently validate every prepared arc/cost against original XML."""
import json,xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from prepared_csr import read,U64
R=Path(__file__).resolve().parents[1];E=R/'experiments'
B=E/'full_ram_length_switch_prediction_v1_2026-10-09'
D=E/'full_ram_length_switch_csr_verification_v1_2026-10-09';D.mkdir(exist_ok=False)
graph=E/'full_ram_comb_only_route_v1_2026-10-09/rr_graph.xml'
m,f=read(B/'csr',sha(graph));ids=f['node_ids'];rank={n:i for i,n in enumerate(ids)}
costs={};topology={}
for row,n in enumerate(ids):
    for slot in range(f['row_offsets'][row],f['row_offsets'][row+1]):
        eid=f['edge_ids'][slot];topology[eid]=(n,ids[f['dest_ranks'][slot]],f['switch_ids'][slot]);costs[eid]=f['costs'][slot]
nodes={};delays={};edge=0;disabled=0;stack=[]
for event,x in ET.iterparse(graph,events=['start','end']):
    if event=='start':stack.append(x);continue
    parent=stack[-2].tag if len(stack)>1 else None
    if x.tag=='switch' and parent=='switches':
        timing=x.find('timing');value=Fraction(timing.get('Tdel','0')) if timing is not None else Fraction(0)
        assert value>=0;scaled=value*10**12
        delays[int(x.get('id'))]=(2*scaled.numerator+scaled.denominator)//(2*scaled.denominator)
    if x.tag=='node' and parent=='rr_nodes':
        n=int(x.get('id'));cap=int(x.get('capacity'));loc=x.find('loc')
        length=max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))+1 if x.get('type') in ('CHANX','CHANY') else 0
        nodes[n]=(cap,length);assert f['capacities'][rank[n]]==cap
    if x.tag=='edge' and parent=='rr_edges':
        src,dst,switch=(int(x.get(k)) for k in ('src_node','sink_node','switch_id'))
        assert topology[edge]==(src,dst,switch)
        expected=1+256*nodes[dst][1]+delays[switch] if nodes[dst][0]>0 else U64
        assert costs[edge]==expected
        disabled+=expected==U64;edge+=1
    if (x.tag,parent) in [('switch','switches'),('node','rr_nodes'),('edge','rr_edges')]:stack[-2].remove(x);x.clear()
    stack.pop()
assert len(nodes)==m['nodes'] and edge==m['edges']
out=dict(passed=True,nodes=len(nodes),edges_checked=edge,disabled_arcs=disabled,
    bindings={str(p):sha(p) for p in [Path(__file__),graph,B/'protocol.json',B/'csr/manifest.json']},
    scope='Independent original XML arc identity/capacity and exact uncalibrated 1+256*destination channel span+switch-delay ps costs; no RC/timing calibration, shortest-path optimality or target-label use.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(out['nodes'],edge,'all CSR costs match XML')
