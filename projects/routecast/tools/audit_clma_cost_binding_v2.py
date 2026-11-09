"""Audit the actual native per-node CSV and full base-cost arc parity."""
import json,shutil,time
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from bound_indexed_cost import BoundIndexedCost
from native_indexed_cost import NativeBaseSketch,parse_cost_echo
out=Path('experiments/clma_cost_binding_audit_v2_2026-10-04')
if out.exists():raise ValueError('fresh output required')
parent=Path('experiments/clma_cost_binding_2026-10-04');proto=json.loads((parent/'protocol.json').read_text());receipt=json.loads((parent/'receipt.json').read_text());assert receipt['exit_code']==0 and receipt['input_hashes_unchanged'];assert receipt['protocol_sha256']==sha(parent/'protocol.json')
inputs={**proto['inputs'],'table':{'path':str((parent/'rr_indexed_data.echo').resolve()),'sha256':receipt['reports']['rr_indexed_data.echo']},'binding':{'path':str((parent/'routecast_node_cost_indices.csv').resolve()),'sha256':receipt['reports']['routecast_node_cost_indices.csv']}}
assert all(sha(v['path'])==v['sha256'] for v in inputs.values());out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
p={'inputs':inputs,'scope':'clma native export coverage and complete base-arc parity; not real multi-segment/family accuracy validation','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');start=time.monotonic();g=read_rr_graph(inputs['graph']['path']);text=Path(inputs['table']['path']).read_text();csv=Path(inputs['binding']['path']).read_text();identity={'graph_sha256':g.sha256,'table_sha256':inputs['table']['sha256'],'bindings_sha256':inputs['binding']['sha256']};bound=BoundIndexedCost(g,text,csv,identity);old=NativeBaseSketch(g,text,g.sha256)
assert bound.node_costs==old.node_costs and bound.outgoing==old.outgoing;norm,rows=parse_cost_echo(text);bytype={r['type']:r['base'] for r in rows.values()};assert all(bound.rows[index]['base']==bytype[g.nodes[n].type] for n,index in bound.indices.items())
assert all(sha(v['path'])==v['sha256'] for v in inputs.values());(out/'binding_identity.json').write_text(json.dumps(identity,indent=2)+'\n');r={'protocol_sha256':sha(out/'protocol.json'),'native_export_nodes':len(bound.indices),'physical_graph_nodes':len(g.nodes),'physical_graph_edges':len(g.edges),'native_index_counts':dict(Counter(bound.indices.values())),'complete_node_and_arc_cost_parity':True,'unrounded_normalized_base_values_exact_old_classes':True,'normalized_RC_scope':'base mapping algebra checked, not full RC model/search replay','native_indexed_echo_exact_prior':inputs['table']['sha256']==sha(Path('experiments/clma_base_echo_2026-10-04/rr_indexed_data.echo')),'wall_s':time.monotonic()-start,'inputs_unchanged':True,'binding_identity_sha256':sha(out/'binding_identity.json')};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
