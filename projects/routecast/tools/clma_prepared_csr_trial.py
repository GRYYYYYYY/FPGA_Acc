"""Full real clma physical-ID and integer-cost transport roundtrip."""
import json,time,shutil
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from cached_bound_rc import CachedBoundRC
from prepared_csr import write,read,U64
out=Path('experiments/clma_prepared_csr_2026-10-04');cap=Path('experiments/clma_cost_binding_2026-10-04')
if out.exists():raise ValueError('fresh output required')
p=json.loads((cap/'protocol.json').read_text());r=json.loads((cap/'receipt.json').read_text());inputs={'graph':p['inputs']['graph'],'table':{'path':str((cap/'rr_indexed_data.echo').resolve()),'sha256':r['reports']['rr_indexed_data.echo']},'binding':{'path':str((cap/'routecast_node_cost_indices.csv').resolve()),'sha256':r['reports']['routecast_node_cost_indices.csv']}};assert all(sha(v['path'])==v['sha256'] for v in inputs.values());out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
proto={'inputs':inputs,'scope':'full real RR transport roundtrip only; not a C++/HLS kernel or query benchmark','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}};(out/'protocol.json').write_text(json.dumps(proto,indent=2)+'\n');start=time.monotonic();g=read_rr_graph(inputs['graph']['path']);engine=CachedBoundRC(g,Path(inputs['table']['path']).read_text(),Path(inputs['binding']['path']).read_text(),{'graph_sha256':g.sha256,'table_sha256':inputs['table']['sha256'],'bindings_sha256':inputs['binding']['sha256']});build=time.monotonic()-start;start=time.monotonic();manifest=write(engine,out/'csr');export=time.monotonic()-start;start=time.monotonic();m,f=read(out/'csr',g.sha256,manifest['context_sha256']);count=0
for rank,n in enumerate(f['node_ids']):
 lo,hi=f['row_offsets'][rank:rank+2];decoded=tuple((f['edge_ids'][i],f['node_ids'][f['dest_ranks'][i]],None if f['costs'][i]==U64 else f['costs'][i]) for i in range(lo,hi));assert decoded==engine.outgoing[n]
 for i in range(lo,hi):assert f['switch_ids'][i]==g.edges[f['edge_ids'][i]].switch_id
 assert f['capacities'][rank]==g.nodes[n].capacity;count+=hi-lo
assert count==len(g.edges);verify=time.monotonic()-start;assert all(sha(v['path'])==v['sha256'] for v in inputs.values());receipt={'protocol_sha256':sha(out/'protocol.json'),'nodes':len(g.nodes),'edges':count,'complete_topology_rawID_switch_capacity_cost_roundtrip':True,'prepared_build_s':build,'export_s':export,'read_verify_s':verify,'payload_bytes':sum(v['bytes'] for v in manifest['files'].values()),'manifest_sha256':sha(out/'csr/manifest.json'),'context_sha256':m['context_sha256'],'inputs_unchanged':True};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
