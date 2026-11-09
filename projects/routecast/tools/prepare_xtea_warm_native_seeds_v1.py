"""Same frozen whole-NET selector for both certified XTEA model outputs."""
import ast,json,sys,time
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from shared_compact_native_inventory_v1 import Inventory
from serialize_whole_net_subset_pin_index_v2 import serialize_subset
R=Path(__file__).resolve().parents[1]
O=R/'experiments/xtea_warm_native_seed_preparation_v1_2026-10-13';O.mkdir()
epfile=R/'experiments/xtea_swap_native_demand_v1_2026-10-13/endpoints.json';ep=json.loads(epfile.read_text())
selector=R/'tools/select_resident_native_seed_subset_v1.py';bindings=closure([Path(__file__),selector]);bindings[str(epfile)]=sha(epfile)
for spec in ep['inputs'].values():assert sha(spec['path'])==spec['sha256'];bindings[spec['path']]=spec['sha256']
refs={'all':'xtea_warm_update_pair_v1_2026-10-13/all','local':'xtea_warm_update_pair_v1_2026-10-13/local'}
for name,dirname in refs.items():
 model=R/'experiments'/dirname/'model'
 for filename in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
  p=model/filename;v=json.loads(p.read_text());assert v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];assert all(sha(q)==h for q,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
(O/'protocol.json').write_text(json.dumps(dict(bindings=bindings,order=['all','local'],selector=str(selector),scope='Same deterministic wholeNET subset selection and current-pin-index serialization. All omitted connections remain required native routing work. No final-route labels used by selector. Preparation only, no native routing or total-time benefit yet.'),indent=2)+'\n')
xml=Inventory(Path(ep['inputs']['graph']['path']));xml.validate(Path(ep['inputs']['graph']['path']),ep['graph_sha256'])
tree=ast.parse(selector.read_text());loop=next(n for n in tree.body if isinstance(n,ast.For));start=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.For) and ast.unparse(n.target)=='rec');stop=next(i for i,n in enumerate(loop.body) if i>start and isinstance(n,ast.Assert));selection=compile(ast.Module(body=loop.body[start:stop],type_ignores=[]),str(selector),'exec')
rows=[]
for arm,dirname in refs.items():
 tick=time.perf_counter();p=R/'experiments'/dirname/'model/sketch.json';c=json.loads(p.read_text());bindings[str(p)]=sha(p)
 scope=dict(c=c,ep=ep,xml=xml,groups=defaultdict(list),Counter=Counter);exec(selection,scope);records=scope['records'];pending=scope['pending']
 ids={r['connection_id'] for r in records};allids={q['connection_id'] for q in ep['connections']}
 assert len(ids)==len(records) and not ids.intersection(pending) and ids|set(pending)==allids
 ledger=Counter(n for net in scope['kept'] for n in scope['owners'][net]);assert ledger==scope['ledger'] and all(v<=xml.graph.nodes[n].capacity for n,v in ledger.items())
 text,pins=serialize_subset(dict(records=records),epfile,Path(ep['inputs']['native_identity']['path']),Path(ep['inputs']['place']['path']),xml)
 d=O/arm;d.mkdir();(d/'seed.route').write_text(text);(d/'subset.json').write_text(json.dumps(dict(records=records,pending=pending,decisions=scope['decisions']))+'\n');(d/'pin_bindings.json').write_text(json.dumps(pins)+'\n')
 rows.append(dict(arm=arm,selected_connections=len(records),pending_connections=len(pending),required_connections=len(allids),selected_nets=len(scope['kept']),selection_serialization_seconds=time.perf_counter()-tick))
 for p in d.iterdir():bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
(O/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,complete_required_connection_partition_and_subset_capacity_pass=True,scope='Certified predictions serialized using frozen selector; native import, final full legality, canonical reload and QoR still pending.'),indent=2)+'\n');print(json.dumps(rows),flush=True)
