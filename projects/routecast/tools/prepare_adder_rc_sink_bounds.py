"""Prepare full-graph sink RC distances and independently verify certificates."""
import json,time,shutil,sys
from array import array
from pathlib import Path
from prepared_csr import read,U64
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from prepared_integer_rc_context import PreparedIntegerRC
from rc_feasible_cost_region import RCFeasibleCostRegion
from verify_rc_remaining_certificate import verify
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';out=base/'adder_tree_prepared_rc_sink_bounds_2026-10-06';out.mkdir();(out/'sources').mkdir();start=time.perf_counter();bindings={}
def readjson(path):bindings[str(path)]=sha(path);return json.loads(path.read_text())
epfiles=[base/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json']+[base/f'adder_tree_2L032_move_sequence_2026-10-06/step_{i}_endpoints.json' for i in range(1,4)];endpoints=[readjson(p) for p in epfiles];graph=endpoints[0]['graph_sha256'];assert all(x['graph_sha256']==graph for x in endpoints);sinks=sorted({r['sink'] for ep in endpoints for r in ep['connections']});csr=base/'adder_tree_family_length_switch_csr_2026-10-06/adder_tree_2L_032bits/csr';electrical=base/'adder_tree_family_exact_buffered_rc_classes_2026-10-06/adder_tree_2L_032bits';lattice=base/'adder_tree_prepared_integer_rc_2026-10-06'
for folder in (csr,electrical,lattice):
 for p in folder.rglob('*'):
  if p.is_file():bindings[str(p)]=sha(p)
m,f=read(csr,graph);proof=readjson(lattice/'verification.json');rc=PreparedIntegerRC(ExactBufferedRC(f,*load(electrical,graph)),lattice,proof['receipt_sha256']);region=RCFeasibleCostRegion(m['nodes'],[(u,f['dest_ranks'][i],rc.increments[i],f['costs'][i]) for u in range(m['nodes']) for i in range(f['row_offsets'][u],f['row_offsets'][u+1]) if f['costs'][i]!=U64 and f['capacities'][f['dest_ranks'][i]]>0]);rows=[]
if sys.byteorder!='little':raise ValueError('little endian required')
for sink in sinks:
 remaining=region.distance(sink,True);values=[U64]*m['nodes']
 for n,d in remaining.items():
  if not 0<=d<U64:raise ValueError('finite sink distance requires uint64 below sentinel')
  values[n]=d
 certificate=verify(f,rc.increments,sink,values);path=out/f'sink_{sink}.bin';path.write_bytes(array('Q',values).tobytes());rows.append({'sink':sink,'payload':path.name,'sha256':sha(path),'certificate':certificate})
 if len(rows)%20==0:print({'prepared_sinks':len(rows),'total':len(sinks)},flush=True)
for n in ('prepare_adder_rc_sink_bounds.py','verify_rc_remaining_certificate.py','rc_feasible_cost_region.py','prepared_integer_rc_context.py'):shutil.copyfile(root/'tools'/n,out/'sources'/n)
assert all(sha(Path(p))==h for p,h in bindings.items());receipt={'schema':'ROUTECAST_EXACT_RC_SINK_BOUNDS_V1','graph_sha256':graph,'nodes':m['nodes'],'scale':rc.scale,'byteorder':'little','unreachable_sentinel':U64,'inputs_sha256':bindings,'sinks':rows,'sources_sha256':{p.name:sha(p) for p in (out/'sources').iterdir()},'preparation_and_full_certificate_s':time.perf_counter()-start,'total_payload_bytes':sum((out/x['payload']).stat().st_size for x in rows),'scope':'Full N dense uint64 per sink, prepared initial+three fixed endpoint layouts; independent edge inequality and tight-path-to-sink certification. Not subset footprint, no unknown-sink fallback. No runtime or hardware gain claim.'};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print({'sinks':len(rows),'bytes':receipt['total_payload_bytes'],'preparation_s':receipt['preparation_and_full_certificate_s'],'receipt_sha256':sha(out/'receipt.json')})
