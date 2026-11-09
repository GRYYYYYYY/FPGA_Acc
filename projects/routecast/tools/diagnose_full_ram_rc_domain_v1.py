"""Full input graph RC support diagnosis, no route labels."""
import json,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from path_rc import PathRC,State
from fractions import Fraction
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_ram_rc_domain_v1_2026-10-09';D.mkdir(exist_ok=False)
p=E/'full_ram_comb_only_route_v1_2026-10-09/rr_graph.xml';g=read_rr_graph(p);rc=PathRC(g)
types=Counter();nonbuffered=Counter();classes={};negative=[]
for eid,e in enumerate(g.edges):
 root=ET.fromstring(g.switches[e.switch_id]) if e.switch_id not in classes else None
 if root is not None:classes[e.switch_id]=root.get('type')
 types[classes[e.switch_id]]+=1
 if not rc.switches[e.switch_id][0]:nonbuffered[(g.nodes[e.source].type,g.nodes[e.sink].type)]+=1
# Physical RC increments depend only on source R, destination R/C and switch fields when buffered.
seen={}
for eid,e in enumerate(g.edges):
 key=(rc.nodes[e.source][0],rc.nodes[e.sink],e.switch_id)
 if key in seen:continue
 value=rc.step(State(Fraction(0),Fraction(0)),eid).delay;seen[key]=value
 if value<0:negative.append(eid)
out=dict(nodes=len(g.nodes),edges=len(g.edges),switch_edge_types=dict(types),nonbuffered_edge_endpoint_types={str(k):v for k,v in nonbuffered.items()},distinct_local_rc_classes=len(seen),negative_zero_start_increment_classes=len(negative),negative_witness_edges=negative[:20],all_switches_buffered=all(x[0] for x in rc.switches.values()),bindings={str(x):sha(x) for x in [p,Path(__file__),R/'tools/path_rc.py',R/'tools/rr_graph.py']},scope='Exact serialized-decimal RC domain diagnosis only. Zero-start local increments do not establish state-independent nonbuffered paths, route-tree STA or native float parity.')
(D/'diagnosis.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
