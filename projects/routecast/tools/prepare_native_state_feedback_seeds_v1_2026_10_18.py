"""Frozen identical selector/current-pin serialization for none/all/local."""
import ast,json,sys,time
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from shared_compact_native_inventory_v1 import Inventory
from serialize_whole_net_subset_pin_index_v2 import serialize_subset
O=R/'experiments/native_state_feedback_seed_preparation_v1_2026-10-18';O.mkdir(exist_ok=False)
epfile=R/'experiments/xtea_native_state_new_swap_v1_2026-10-18/demand/endpoints.json';ep=json.loads(epfile.read_text());selector=R/'tools/select_resident_native_seed_subset_v1.py';ap=R/'experiments/native_state_feedback_audits_v1_2026-10-18/verification.json';v=json.loads(ap.read_text());assert v['all_six_original_XML_fraction_audits_pass'] and all(sha(p)==h for p,h in v['bindings'].items());pp=R/'experiments/xtea_native_state_native_utility_protocol_v1_2026-10-18/protocol.json';protocol=json.loads(pp.read_text());assert all(sha(p)==h for p,h in protocol['bindings'].items());bindings={**closure([Path(__file__),selector]),**v['bindings'],str(ap):sha(ap),str(pp):sha(pp),str(epfile):sha(epfile)}
for spec in ep['inputs'].values():assert sha(spec['path'])==spec['sha256'];bindings[spec['path']]=spec['sha256']
root=R/'experiments/xtea_native_state_feedback_comparison_v3_2026-10-18';frames={'none':root/'none/initial.json','all':root/'all/sketch.json','local':root/'local/sketch.json'}
with (O/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,frames={k:str(v) for k,v in frames.items()},scope='Frozen same selector and native current pins; all omitted connections remain required.'),f,indent=2);f.write('\n')
xml=Inventory(Path(ep['inputs']['graph']['path']));xml.validate(Path(ep['inputs']['graph']['path']),ep['graph_sha256']);tree=ast.parse(selector.read_text());loop=next(n for n in tree.body if isinstance(n,ast.For));start=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.For) and ast.unparse(n.target)=='rec');stop=next(i for i,n in enumerate(loop.body) if i>start and isinstance(n,ast.Assert));selection=compile(ast.Module(body=loop.body[start:stop],type_ignores=[]),str(selector),'exec');rows=[]
for arm,path in frames.items():
 tick=time.perf_counter();c=json.loads(path.read_text());bindings[str(path)]=sha(path);scope=dict(c=c,ep=ep,xml=xml,groups=defaultdict(list),Counter=Counter);exec(selection,scope);records=scope['records'];pending=scope['pending'];ids={r['connection_id'] for r in records};allids={q['connection_id'] for q in ep['connections']};assert len(ids)==len(records) and not ids.intersection(pending) and ids|set(pending)==allids;ledger=Counter(n for net in scope['kept'] for n in scope['owners'][net]);assert ledger==scope['ledger'] and all(v<=xml.graph.nodes[n].capacity for n,v in ledger.items());text,pins=serialize_subset(dict(records=records),epfile,Path(ep['inputs']['native_identity']['path']),Path(ep['inputs']['place']['path']),xml);d=O/arm;d.mkdir()
 for name,data in [('seed.route',text),('subset.json',json.dumps(dict(records=records,pending=pending,decisions=scope['decisions']))+'\n'),('pin_bindings.json',json.dumps(pins)+'\n')]:
  with (d/name).open('x') as f:f.write(data)
  bindings[str(d/name)]=sha(d/name)
 rows.append(dict(arm=arm,selected_connections=len(records),pending_connections=len(pending),selected_nets=len(scope['kept']),selection_seconds=time.perf_counter()-tick))
assert all(sha(p)==h for p,h in bindings.items())
with (O/'verification.json').open('x') as f:json.dump(dict(bindings=bindings,rows=rows,complete_required_connection_partition_and_subset_capacity_pass=True,scope='Seed production; independent audit and native utility pending.'),f,indent=2);f.write('\n')
print(rows,flush=True)
