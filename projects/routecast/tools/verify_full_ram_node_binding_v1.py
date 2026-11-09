"""Full native-export provenance and node-index validation."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from bound_indexed_cost import validate_binding,digest
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_ram_native_node_binding_verification_v1_2026-10-09';D.mkdir(exist_ok=False)
B=E/'full_ram_native_node_binding_v1_2026-10-09';r=json.loads((B/'receipt.json').read_text());assert r['exit_code']==0
for p,h in {**r['bindings'],**r['files']}.items():assert sha(p)==h
build=R/'build/cost_binding_export_2026-10-04';bp=json.loads((build/'protocol.json').read_text())
for p,h in bp['shared_libraries'].items():assert sha(p)==h
for p,h in bp['source_sha256'].items():assert sha(p)==h
source=R/'tools/native_cost_binding/main.cpp'
assert 'device.rr_graph.node_cost_index(node)' in source.read_text()
assert 'device.rr_indexed_data[index].seg_index' in source.read_text()
original=E/'full_ram_comb_only_route_v1_2026-10-09/rr_graph.xml'
assert sha(B/'rr_graph.xml')==sha(original)
g=read_rr_graph(original);table=(B/'rr_indexed_data.echo').read_text();csv=(B/'routecast_node_cost_indices.csv').read_text()
identity=dict(graph_sha256=g.sha256,table_sha256=digest(table),bindings_sha256=digest(csv))
norm,rows,indices,bound=validate_binding(g,table,csv,identity)
from collections import Counter
out=dict(passed=True,nodes=len(indices),classes=len(rows),normalization=str(norm),node_class_counts=dict(Counter(indices.values())),identity=identity,bindings={str(p):sha(p) for p in [Path(__file__),B/'receipt.json',B/'protocol.json',original,B/'rr_indexed_data.echo',B/'routecast_node_cost_indices.csv',build/'protocol.json',build/'receipt.json',source,R/'tools/bound_indexed_cost.py']},scope='Native API node_cost_index/seg_index export, authenticated private-main build and unchanged linked archives; explicit graph load/no reorder. Export structural validation not native float timing parity, complete route quality audit or unseen-family evidence.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
