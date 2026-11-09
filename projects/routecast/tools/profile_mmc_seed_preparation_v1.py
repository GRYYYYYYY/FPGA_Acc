"""Profile exact existing seed selection/serialization; no native runs or policy changes."""
import ast,json,sys,time,resource
from pathlib import Path
from collections import defaultdict,Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from shared_compact_native_inventory_v1 import Inventory
from serialize_whole_net_subset_pin_index_v2 import serialize_subset
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_seed_preparation_profile_v1_2026-10-21';D.mkdir()
old=R/'experiments/mmc_native_local_seed_v1_2026-10-18'
proof=R/'experiments/mmc_native_cached_feedback_audits_v1_2026-10-18/verification.json'
frame=R/'experiments/mmc_native_cached_feedback_pilot_v1_2026-10-18/model/sketch.json'
epf=R/'experiments/mmc_native_state_swap_inputs_v1_2026-10-18/demand/endpoints.json'
selector=R/'tools/select_resident_native_seed_subset_v1.py'
files=[Path(__file__),proof,frame,epf,selector,R/'tools/shared_compact_native_inventory_v1.py',R/'tools/serialize_whole_net_subset_pin_index_v2.py',old/'receipt.json',old/'subset.json',old/'seed.route',old/'pin_bindings.json']
bindings={str(p):sha(p) for p in files}
(D/'protocol.json').write_text(json.dumps({'bindings':bindings,'scope':'One exposed frozen MMC frame exact replay. Whole-byte input checks retained, graph loaded once; no model/native/heldout performance claim. Outputs must equal original subset/pins/route exactly. Stage timings include guards and output production; baseline proof checks charged.','native_calls':0},indent=2)+'\n')
rows=[];start=time.perf_counter();tick=start
def stage(name):
 global tick
 now=time.perf_counter();rows.append({'stage':name,'seconds':now-tick});tick=now;print(name,rows[-1]['seconds'],flush=True)
v=json.loads(proof.read_text());assert v['all_three_frame_and_complete_event_audits_pass']
assert all(sha(p)==h for p,h in v['bindings'].items())
stage('source_proof_integrity')
ep=json.loads(epf.read_text());c=json.loads(frame.read_text())
for spec in ep['inputs'].values():assert sha(spec['path'])==spec['sha256']
stage('frame_endpoint_decode_and_input_hashes')
xml=Inventory(Path(ep['inputs']['graph']['path']));xml.validate(Path(ep['inputs']['graph']['path']),ep['graph_sha256'])
stage('inventory_load_and_validation')
tree=ast.parse(selector.read_text());loop=next(n for n in tree.body if isinstance(n,ast.For));begin=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.For) and ast.unparse(n.target)=='rec');end=next(i for i,n in enumerate(loop.body) if i>begin and isinstance(n,ast.Assert))
code=compile(ast.Module(body=loop.body[begin:end],type_ignores=[]),str(selector),'exec');scope=dict(c=c,ep=ep,xml=xml,groups=defaultdict(list),Counter=Counter);exec(code,scope)
records=scope['records'];pending=scope['pending'];ids={r['connection_id'] for r in records};allids={q['connection_id'] for q in ep['connections']}
assert len(ids)==len(records) and not ids.intersection(pending) and ids|set(pending)==allids
ledger=Counter(n for net in scope['kept'] for n in scope['owners'][net]);assert ledger==scope['ledger'] and all(v<=xml.graph.nodes[n].capacity for n,v in ledger.items())
stage('whole_NET_selection_and_capacity_partition')
text,pins=serialize_subset({'records':records},epf,Path(ep['inputs']['native_identity']['path']),Path(ep['inputs']['place']['path']),xml)
stage('serializer_with_graph_hash_guards')
subset={'records':records,'pending':pending,'decisions':scope['decisions']}
for name,data in [('seed.route',text),('subset.json',json.dumps(subset)+'\n'),('pin_bindings.json',json.dumps(pins)+'\n')]:
 (D/name).write_text(data)
stage('output_encoding_and_write')
assert (D/'seed.route').read_bytes()==(old/'seed.route').read_bytes()
assert subset==json.loads((old/'subset.json').read_text()) and pins=={int(k):v for k,v in json.loads((old/'pin_bindings.json').read_text()).items()}
assert all(sha(p)==h for p,h in bindings.items())
stage('output_parity_and_final_input_integrity')
result={'stages':rows,'total_profile_seconds':time.perf_counter()-start,'peak_RSS_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'route_bytes_exact':True,'subset_and_pin_bindings_exact':True,'bindings':bindings,'scope':'Measured exact prepared seed replay only. Protocol freezing excluded; model/native/full gate and source capture excluded. Inventory is rebuilt, not a warm resident speed measurement. No end-to-end or unseen gain.'}
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('EXACT REPLAY PASS',result['total_profile_seconds'],flush=True)
