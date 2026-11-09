"""Authenticated real observer-state copy cost, not a live search or workflow gain."""
import json,sys,time,copy,statistics
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from observer_state_clone_v1 import clone_state
parent=R/'experiments/mcnc_pending_swap_transactions16_v17_2026-10-07';out=R/'experiments/observer_clone_cost_v1_2026-10-07';out.mkdir();rp=parent/'receipt.json';r=json.loads(rp.read_text());row=next(x for x in r['rows'] if x['name']=='dsip');files=sorted((parent/'dsip').glob('repair_batch4_attempt1_branch*/net*.json'));assert len(files)==247;bindings={**closure([Path(__file__)]),str(rp):sha(rp)}
for file in files:assert sha(file)==row['files'][str(file)];bindings[str(file)]=sha(file)
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='247 archived JSON-valued group states of authenticated dsip batch4, four alternating deepcopy/typed-copy pairs. Parse outside timing, allocation/copy only, equality and mutation audit outside. Not live aggregate alias preservation, caller arbitrary Python objects, CPU profile or full workflow gain.'))+'\n');states=[json.loads(p.read_text()) for p in files];rows=[]
for repeat in range(4):
 for name,fn in ([('old',copy.deepcopy),('new',clone_state)] if repeat%2==0 else [('new',clone_state),('old',copy.deepcopy)]):
  start=time.perf_counter();copies=[fn(state) for state in states];elapsed=time.perf_counter()-start;assert copies==states
  for state,cloned in zip(states,copies):
   assert cloned is not state and cloned['records'] is not state['records'] and cloned['ledger'] is not state['ledger']
   if cloned['records']:
    c=cloned['records'][0];o=state['records'][0];assert c is not o and c['answer'] is not o['answer'] and c['answer']['physical_edge_ids'] is not o['answer']['physical_edge_ids'];c['answer']['physical_edge_ids'].append(-1);assert -1 not in o['answer']['physical_edge_ids']
  del copies;rows.append(dict(repeat=repeat,version=name,seconds=elapsed,states=247));print(rows[-1],flush=True)
fixture={'records':[{'answer':{'physical_edge_ids':[1],'nested':{'list':[2]}},'extra':{'list':[3]}}],'ledger':{1:1},'failure':{'query':{'data':[4]}}};clone=clone_state(fixture);assert clone==fixture;clone['records'][0]['extra']['list'].append(9);clone['records'][0]['answer']['nested']['list'].append(9);clone['failure']['query']['data'].append(9);assert fixture['records'][0]['extra']['list']==[3] and fixture['records'][0]['answer']['nested']['list']==[2] and fixture['failure']['query']['data']==[4];assert clone_state(None) is None
assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows,median_seconds={n:statistics.median(x['seconds'] for x in rows if x['version']==n) for n in ('old','new')},all_json_values_equal=True,mutable_paths_and_nested_metadata_isolated=True,bindings=bindings),indent=2)+'\n')
