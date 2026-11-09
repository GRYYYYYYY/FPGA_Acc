"""Compare full-edge exact lattice reconstruction with unique-pair reconstruction."""
import json,time
from math import lcm
from pathlib import Path
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
from exact_rc_lattice_unique_pairs_v1 import exact_scale
R=Path(__file__).resolve().parents[1];P=R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/protocol.json'
g=json.loads(P.read_text())['inputs']['rr_graph'];ctx=ImmutableXMLAudit(g['path'],g['sha256']);ids,classes,switches,digest=read(g['path']);assert digest==ctx.digest
start=time.perf_counter();old=1
for n in ids:
 a,b=classes[n];old=lcm(old,(a*b/2).denominator)
for eid in range(len(ctx.graph.edges)):
 e=ctx.graph.edges[eid];old=lcm(old,arc_delay(classes,switches,ids[e.sink],e.switch_id).denominator)
old_s=time.perf_counter()-start
start=time.perf_counter();new,pairs=exact_scale(ids,classes,switches,ctx.graph.edges);new_s=time.perf_counter()-start
assert old==new and sha(g['path'])==digest
D=R/'experiments/exact_rc_lattice_unique_pairs_v1_2026-10-09';D.mkdir(exist_ok=True)
out=dict(graph_sha256=digest,nodes=len(ids),edges=len(ctx.graph.edges),used_node_classes=len(set(ids)),unique_electrical_edge_pairs=pairs,old_scale=old,new_scale=new,exact_full_edge_scale_equal=True,seconds=dict(full_edge_fraction_lcm=old_s,unique_pair_fraction_lcm=new_s),bindings={str(p):sha(p) for p in [P,Path(__file__),R/'tools/exact_rc_lattice_unique_pairs_v1.py']},scope='One real adder RR graph exact integer equality. No skipped physical path validation. Not integrated into v7, not an MMC or full-workflow speedup. Graph and RC load costs remain required.')
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
