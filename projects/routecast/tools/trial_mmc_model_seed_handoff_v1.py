"""Charged same-call model-to-seed handoff; all original outputs/guards retained."""
import ast,json,time
from pathlib import Path
from collections import defaultdict,Counter
from pre_route_endpoints import sha
from model_inventory_snapshot_v1 import capture
from serialize_whole_net_subset_pin_index_v2 import serialize_subset
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_model_seed_handoff_v1_2026-10-21';D.mkdir()
P=R/'experiments/mmc_native_cached_feedback_pilot_v1_2026-10-18/protocol.json';p=json.loads(P.read_text());assert all(sha(k)==v for k,v in p['bindings'].items())
source=Path(p['command'][1]);selector=R/'tools/select_resident_native_seed_subset_v1.py';extra=[Path(__file__),P,R/'tools/model_inventory_snapshot_v1.py',R/'tests/test_model_inventory_snapshot_v1.py',selector,R/'tools/serialize_whole_net_subset_pin_index_v2.py']
bindings={**p['bindings'],**{str(f):sha(f) for f in extra}}
(D/'protocol.json').write_text(json.dumps({'bindings':bindings,'scope':'One same-call MMC model -> immutable snapshot -> unchanged wholeNET selector/serializer. Only model result gains the final in-memory candidate. Full model output and guards remain. Counts setup, snapshot, selection, serializer, writes and parity separately. No native calls, warm-state/e2e/heldout speed claim. Cached floors/source-contract inherited.','native_calls':0},indent=2)+'\n')
tree=ast.parse(source.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='predict');matches=0
for n in fn.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='result' for t in n.targets):
  assert isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='dict';n.value.keywords.append(ast.keyword(arg='handoff_frame',value=ast.Name(id='candidate',ctx=ast.Load())));matches+=1
assert matches==1;ast.fix_missing_locations(tree);ns={'__file__':str(source),'__name__':'mmc_handoff_original'};exec(compile(tree,str(source),'exec'),ns)
rows=[];start=time.perf_counter();tick=start
def stage(name):
 global tick
 now=time.perf_counter();rows.append({'stage':name,'seconds':now-tick});tick=now;print(name,rows[-1]['seconds'],flush=True)
args=p['command'][2:];old_model=Path(args[1]);args[1]=str(D/'model');result,context=ns['predict'](*args,retain_context=True);stage('complete_original_model_and_outputs')
graph,digest,nodes,fields=context;snapshot=capture(graph,digest,nodes,fields);stage('owned_snapshot_and_full_graph_hashes')
epf=Path(args[0]);ep=json.loads(epf.read_text());c=result['handoff_frame']
for spec in ep['inputs'].values():assert sha(spec['path'])==spec['sha256']
# The frozen selector's original AST is executed without importing its experiment driver.
t=ast.parse(selector.read_text());loop=next(n for n in t.body if isinstance(n,ast.For));begin=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.For) and ast.unparse(n.target)=='rec');end=next(i for i,n in enumerate(loop.body) if i>begin and isinstance(n,ast.Assert))
scope=dict(c=c,ep=ep,xml=snapshot,groups=defaultdict(list),Counter=Counter);exec(compile(ast.Module(body=loop.body[begin:end],type_ignores=[]),str(selector),'exec'),scope)
records=scope['records'];pending=scope['pending'];ids={r['connection_id'] for r in records};allids={q['connection_id'] for q in ep['connections']};assert len(ids)==len(records) and not ids.intersection(pending) and ids|set(pending)==allids
ledger=Counter(n for net in scope['kept'] for n in scope['owners'][net]);assert ledger==scope['ledger'] and all(v<=snapshot.graph.nodes[n].capacity for n,v in ledger.items());stage('input_reauthentication_and_unchanged_selection')
text,pins=serialize_subset({'records':records},epf,Path(ep['inputs']['native_identity']['path']),Path(ep['inputs']['place']['path']),snapshot);stage('unchanged_serializer_and_graph_guards')
subset={'records':records,'pending':pending,'decisions':scope['decisions']}
for name,data in [('seed.route',text),('subset.json',json.dumps(subset)+'\n'),('pin_bindings.json',json.dumps(pins)+'\n')]: (D/name).write_text(data)
stage('seed_output_encoding_and_write')
old=R/'experiments/mmc_native_local_seed_v1_2026-10-18';assert (D/'seed.route').read_bytes()==(old/'seed.route').read_bytes();assert subset==json.loads((old/'subset.json').read_text());assert pins=={int(k):v for k,v in json.loads((old/'pin_bindings.json').read_text()).items()}
for name in ['initial.json','floors.json','round0.json','round1.json','sketch.json','structural_cost_metrics.json']:assert sha(old_model/name)==sha(D/'model'/name),name
before=json.loads((old_model/'receipt.json').read_text());after=json.loads((D/'model/receipt.json').read_text());semantic=lambda rs:[{k:v for k,v in r.items() if k not in ['seconds','state_file']} for r in rs];assert semantic(before['rounds'])==semantic(after['rounds'])
assert all(sha(k)==v for k,v in bindings.items());stage('complete_state_event_seed_parity_and_final_guards')
receipt={'stages':rows,'total_measured_seconds':time.perf_counter()-start,'complete_state_bytes_exact':True,'round_events_exact':True,'seed_bytes_exact':True,'subset_and_pins_exact':True,'bindings':{**bindings,str(D/'seed.route'):sha(D/'seed.route'),str(D/'model/receipt.json'):sha(D/'model/receipt.json')},'scope':'Charged same-call handoff correctness trial; protocol freezing excluded, model setup/output included, source/floor capture and independent native/canonical gates excluded. No matched baseline or end-to-end speed claim. Snapshot is immutable serial graph transport, not concurrent epoch or model state reuse.'}
(D/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print('INTEGRATED MODEL SEED EXACT PARITY PASS',receipt['total_measured_seconds'],flush=True)
