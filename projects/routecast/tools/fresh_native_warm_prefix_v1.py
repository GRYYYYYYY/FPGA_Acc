"""Actual fresh raw prefix with shared local RR/RC and explicit warm provenance."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from source_binding_v2 import closure
from persistent_raw_compiled_session_v1 import Session as RawSession
from soft_demand_workspace_bridge_v1 import Search
R=Path(__file__).resolve().parents[1]

class Prefix(RawSession):
 def predict(self,*args,**kwargs):
  parent=self.parent
  if parent.closed or parent.active or parent.owner.state is not self.source_state or parent.owner.generation!=self.generation:raise RuntimeError('stale shared prefix source')
  return super().predict(*args,**kwargs)

def shared_prefix(parent,endpoint,route):
 tick=time.perf_counter()
 if parent.closed or parent.active or parent.owner.state is not parent.checkpoint.state or parent.owner.generation!=parent.checkpoint.generation:raise RuntimeError('source checkpoint lifecycle')
 p=object.__new__(Prefix);p.parent=parent;p.source_state=parent.owner.state;p.closed=False;p.active=False;p.generation=parent.owner.generation
 p.sources={**closure([Path(__file__)]),**parent.sources};p.source_endpoint=Path(endpoint).resolve();p.source_hash=sha(p.source_endpoint);p.old=json.loads(p.source_endpoint.read_text());p.route=Path(route).resolve();p.route_hash=sha(p.route)
 if parent.checkpoint.bindings.get(str(p.source_endpoint))!=p.source_hash or parent.checkpoint.bindings.get(str(p.route))!=p.route_hash:raise ValueError('prefix source certificate mismatch')
 p.graph=parent.graph;p.digest=parent.digest;p.nodes=parent.nodes;p.fields=parent.fields;p.rc=parent.rc;p.state=parent.owner.state.paths;p.oldq={q['connection_id']:q for q in p.old['connections']};p.ledger=parent.owner.state.occupancy
 if set(p.oldq)!=set(p.state):raise ValueError('prefix source coverage')
 p.nativerows={}
 for cid,text in parent.checkpoint.records.items():
  record=json.loads(text);q=p.oldq[cid]
  if (record['net_id'],record['source'],record['sink'])!=(q['net_id'],q['source'],q['sink']):raise ValueError('prefix source endpoint')
  p.nativerows[cid]=dict(connection_id=cid,physical_edge_ids=tuple(record['answer']['physical_edge_ids']),delay_integer=record['answer']['delay'])
 p.binary=R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so';cp=R/'experiments/soft_demand_workspace_radix_contract_v3_2026-10-08/verification.json';c=json.loads(cp.read_text())
 if c['random_graphs']!=200 or c['sequential_searches_full_raw_parent_edge_and_settled_arrays_equal']!=2400 or c['bindings'][str(p.binary)]!=sha(p.binary) or not all(sha(path)==h for path,h in c['bindings'].items()):raise ValueError('raw engine contract changed')
 p.sources.update({**c['bindings'],str(cp):sha(cp),str(p.binary):sha(p.binary)})
 p.engine=Search(p.fields,p.rc,p.binary);p.engine.prepare({},0);p.calls=0;p.cold_seconds=time.perf_counter()-tick
 return p

def prepare_layout(original_recipe,output):
 original_recipe=Path(original_recipe).resolve();output=Path(output).resolve();proof_path=original_recipe.with_suffix('.proof.json');proof=json.loads(proof_path.read_text())
 if proof['bindings'].get(str(original_recipe))!=sha(original_recipe) or not all(sha(p)==h for p,h in proof['bindings'].items()):raise ValueError('layout provenance changed')
 payload=json.loads(original_recipe.read_text());payload.pop('dirty_records');assert 'dirty_records' not in payload
 with output.open('x') as f:json.dump(payload,f);f.write('\n')
 with output.with_suffix('.proof.json').open('x') as f:json.dump(dict(bindings={**proof['bindings'],str(proof_path):sha(proof_path),str(output):sha(output)},layout=str(output),route_or_floor_values_present=False),f,indent=2)
 return output

def assemble(parent,prefix,endpoint,raw_directory,layout_path,output):
 tick=time.perf_counter();endpoint=Path(endpoint).resolve();raw_directory=Path(raw_directory).resolve();output=Path(output).resolve();output.mkdir(exist_ok=False)
 rp=raw_directory/'receipt.json';r=json.loads(rp.read_text());initial=raw_directory/'initial.json';before=sha(initial);frame=json.loads(initial.read_text())
 if r['source_generation']!=parent.owner.generation or r['calls']!=prefix.calls:raise ValueError('raw prefix generation/call mismatch')
 if r['bindings'].get(str(endpoint))!=sha(endpoint) or r['bindings'].get(str(prefix.route))!=parent.checkpoint.bindings.get(str(prefix.route)):raise ValueError('prefix source/target binding mismatch')
 if not all(sha(p)==h for p,h in r['bindings'].items()):raise ValueError('fresh raw dependency changed')
 lp=Path(layout_path).resolve();lproof=lp.with_suffix('.proof.json');l=json.loads(lproof.read_text())
 if l['bindings'].get(str(lp))!=sha(lp) or not all(sha(p)==h for p,h in l['bindings'].items()):raise ValueError('layout changed')
 payload=json.loads(lp.read_text());assert 'dirty_records' not in payload
 parent.acquire(endpoint)
 try:
  queries=parent.current_queries;records={x['connection_id']:x for x in frame['records']}
  if len(records)!=len(frame['records']) or set(records)!=set(queries):raise ValueError('fresh raw record coverage')
  for cid,q in queries.items():
   x=records[cid]
   if (x['net_id'],x['source'],x['sink'])!=(q['net_id'],q['source'],q['sink']):raise ValueError('fresh raw endpoint')
  dirty={q['net_id'] for cid,q in queries.items() if (q['source'],q['sink'])!=(parent.owner.state.queries[cid]['source'],parent.owner.state.queries[cid]['sink'])}
  payload['dirty_records']=[dict(x,proxy_budget_integer=x['budget_integer']) for x in frame['records'] if x['net_id'] in dirty]
  warm=parent.checkpoint._build(payload,dirty)
 finally:parent.release()
 encoded=json.dumps(warm)+'\n';wp=output/'initial.json'
 with wp.open('x') as f:f.write(encoded)
 floors={}
 for x in warm['records']:
  key=x['source'],x['sink'];value=x['floor_integer']
  if key in floors and floors[key]!=value:raise ValueError('inconsistent floor')
  floors[key]=value
 with (output/'floors.json').open('x') as f:json.dump([dict(source=s,sink=t,minimum_integer=v) for (s,t),v in sorted(floors.items())],f);f.write('\n')
 with (output/'history.json').open('x') as f:json.dump({},f)
 recipe=output/'dirty_recipe.json'
 with recipe.open('x') as f:json.dump(payload,f);f.write('\n')
 bindings={**parent.checkpoint.bindings,**r['bindings'],**l['bindings'],**closure([Path(__file__)]),str(rp):sha(rp),str(initial):before,str(lproof):sha(lproof)}
 for c in r['certificates']:
  if sha(c['path'])!=c['sha256']:raise ValueError('fresh certificate changed')
  bindings[c['path']]=c['sha256']
 for p in [wp,output/'floors.json',output/'history.json']:bindings[str(p)]=sha(p)
 if sha(initial)!=before or sha(wp)!=payload['expected_initial_sha256']:raise ValueError('fresh warm frame equivalence failed')
 proof=output/'verification.json'
 with proof.open('x') as f:json.dump(dict(schema='NATIVE_ANCHORED_WARM_INPUT_V1',bindings=bindings,endpoint=str(endpoint),dirty_nets=sorted(dirty),native_staged_state_independent_xml_pass=True,zero_initial_history=True,native_anchored_budget_policy='NATIVE_ANCHORED_PROXY_V1',all_old_per_design_minima_independently_recertified=False,fresh_dirty_records=len(payload['dirty_records']),equivalence_to_bound_certified_initial_sha=sha(wp),scope='Fresh raw computed dirty records plus retained source. Complete warm frame equals bound independent certified fixture; reference supplies serialization layout/SHA only. Cached oldF scope unchanged.'),f,indent=2)
 bindings={**bindings,str(proof):sha(proof),str(recipe):sha(recipe)}
 with recipe.with_suffix('.proof.json').open('x') as f:json.dump(dict(bindings=bindings,recipe=str(recipe),fresh_raw_prefix_receipt=str(rp)),f,indent=2)
 parent._fresh_stage=dict(encoded=encoded,recipe=str(recipe),recipe_hash=sha(recipe),bindings={**bindings,str(recipe.with_suffix('.proof.json')):sha(recipe.with_suffix('.proof.json'))},source_state=parent.owner.state,generation=parent.owner.generation,prefix_calls=prefix.calls,dirty=dirty)
 return dict(warm_directory=str(output),recipe=str(recipe),fresh_dirty_records=len(payload['dirty_records']),assembly_seconds=time.perf_counter()-tick)
