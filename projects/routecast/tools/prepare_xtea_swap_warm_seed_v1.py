"""Preserve old unaffected routes; recompute only moved closure zero-price floors."""
import json,sys,time
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from class_cached_rc_endpoint_context_v1 import load_endpoints
from load_design_routing_inputs_v2 import load
from sparse_structural_objective_search_v1 import Search
R=Path(__file__).resolve().parents[1];begin=time.perf_counter();bindings=closure([Path(__file__)])
old=R/'experiments/xtea_design_scoped_retained_pipeline_v1_2026-10-13/model';scopefile=R/'experiments/xtea_swap_native_demand_v1_2026-10-13/affected_scope_v1.json';scope=json.loads(scopefile.read_text());bindings.update(scope['bindings']);bindings[str(scopefile)]=sha(scopefile)
for name in ['verification.json','initial_physical_verification.json','sketch_physical_verification.json']:
 p=old/name;v=json.loads(p.read_text());assert v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];bindings.update(v['bindings']);bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
ep=R/'experiments/xtea_swap_native_demand_v1_2026-10-13/endpoints.json';base=R/'experiments/xtea_swap_node_base_v1_2026-10-13/verification.json';crit=R/'experiments/xtea_fixed_timing_epoch_v1_2026-10-13'
graph,digest,nodes,f,rc,queries=load_endpoints(ep);values,cs,extra=load(ep,base,crit,len(nodes),rc.scale);bindings.update(extra)
previous=json.loads((old/'sketch.json').read_text());last=json.loads((old/'round1.json').read_text())
for p in [old/'sketch.json',old/'round1.json']:bindings[str(p)]=sha(p)
dirty=set(scope['affected']['affected_net_ids']);byid={x['connection_id']:x for x in previous['records']};groups=defaultdict(list)
for q in queries:groups[q['net_id']].append(q)
binary=R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so';bindings[str(binary)]=sha(binary)
search=Search(f,rc,binary,values);search.prepare({},0,structural=False);records=[];calls=0;tick=time.perf_counter()
for net,qs in sorted(groups.items()):
 if net not in dirty:
  for q in qs:
   rec=byid[q['connection_id']];assert all(rec[k]==v for k,v in q.items());records.append(rec)
  continue
 src=qs[0]['source'];assert all(q['source']==src for q in qs);dist,parents,settled=search.search(src,{q['sink'] for q in qs});calls+=1
 for q in sorted(qs,key=lambda q:q['connection_id']):
  assert q['sink'] in settled;u=q['sink'];path=[];seen={u}
  while u!=src:
   u,e=parents[u];assert u not in seen;seen.add(u);path.append(f['edge_ids'][e])
  path.reverse();floor=dist[q['sink']];assert rc.path(src,q['sink'],path)==floor
  records.append(dict(q,answer=dict(status='FOUND',physical_edge_ids=path,delay=floor),floor_integer=floor,budget_integer=max(rc.scale//10**9,(3*floor+1)//2)))
search_seconds=time.perf_counter()-tick;search.close();slots={e:i for i,e in enumerate(f['edge_ids'])};owners=defaultdict(set);independent=Counter();floors={}
for rec in records:
 used={rec['source']}|{f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids']};owners[rec['net_id']].update(used);independent.update(used);key=(rec['source'],rec['sink']);assert key not in floors or floors[key]==rec['floor_integer'];floors[key]=rec['floor_integer']
ledger=Counter(n for used in owners.values() for n in used);overflow=sum(max(0,v-f['capacities'][n]) for n,v in ledger.items());epochs={int(n):e+int(int(n) in dirty) for n,e in last['epochs'].items()};assert set(epochs)==set(groups)
frame=dict(previous,records=sorted(records,key=lambda r:r['connection_id']),ledger=dict(ledger),independent_connection_ledger=dict(independent),overflow_units=overflow,overflow_nodes=sum(v>f['capacities'][n] for n,v in ledger.items()),epochs=epochs,scope='Staged moved-placement seed; unaffected old routes retained, affected wholeNETs replaced with fresh exact zero-price paths. Not a live placement commit.')
O=R/'experiments/xtea_swap_warm_seed_v1_2026-10-13';O.mkdir();(O/'initial.json').write_text(json.dumps(frame)+'\n');(O/'floors.json').write_text(json.dumps([dict(source=s,sink=t,minimum_integer=v) for (s,t),v in sorted(floors.items())])+'\n');(O/'history.json').write_text(json.dumps(last['prices'])+'\n')
# Compare fresh computed affected paths/floors with separately certified full recomputation.
full=R/'experiments/xtea_swap_fixed_epoch_full_pipeline_v1_2026-10-13/model';proof=full/'initial_physical_verification.json';v=json.loads(proof.read_text());assert v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];assert all(sha(p)==h for p,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(proof)]=sha(proof);bindings[str(full/'initial.json')]=sha(full/'initial.json');oracle={r['connection_id']:r for r in json.loads((full/'initial.json').read_text())['records']}
assert all(rec==oracle[rec['connection_id']] if rec['net_id'] in dirty else rec==byid[rec['connection_id']] for rec in records)
for p in O.iterdir():bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
(O/'verification.json').write_text(json.dumps(dict(bindings=bindings,endpoint=str(ep),previous_model=str(old),affected_scope=str(scopefile),dirty_nets=sorted(dirty),required_connections=len(records),recomputed_connections=sum(r['net_id'] in dirty for r in records),zero_price_source_search_calls=calls,search_and_record_preparation_seconds=search_seconds,whole_preparation_seconds=time.perf_counter()-begin,old_unaffected_records_exactly_preserved=True,dirty_records_equal_independent_full_initial=True,epochs_carried_and_dirty_bumped=True,history_exactly_previous_round1=True,scope='Shared staged input for allNET/localNET scheduling comparison. Preparation uses49fresh searches, not cached full-recompute paths. Prior model construction amortization and broader timing/congestion refresh remain separate costs.'),indent=2)+'\n')
print('WARM SEED PASS',calls,'NET searches',sum(r['net_id'] in dirty for r in records),'recomputed connections','overflow',overflow,flush=True)
