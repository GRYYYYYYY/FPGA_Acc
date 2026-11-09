"""Finite-template regional repair under a real placement endpoint update."""
import json,hashlib,shutil,time
from pathlib import Path
from rr_graph import read_rr_graph
from connectivity_trial import construct
from hybrid_repair import repair
from lazy_region_search import LazyRegionalSearch
from regional_search_cache import CachedRegionalSearch
from affected_connections import affected
from rr_batch_occupancy import BatchOccupancy
from physical_prediction_audit import audit
from connection_golden import Result

out=Path('experiments/moved_hybrid_serialization_fix_2026-10-04')
if out.exists():raise ValueError('fresh output required')
out.mkdir(parents=True);(out/'source').mkdir();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
paths={'old_endpoints':Path('experiments/pre_route_endpoints_2026-10-04/diffeq_endpoints.json'),'new_endpoints':Path('experiments/diffeq_placement_swap_2026-10-04/endpoints.json'),'old_candidate':Path('experiments/connectivity_trial_2026-10-04/refinement_2.json')}
new=json.loads(paths['new_endpoints'].read_text());paths['graph']=Path(new['inputs']['graph']['path'])
names=['moved_hybrid_trial.py','rr_graph.py','connectivity_trial.py','hybrid_repair.py','lazy_region_search.py','regional_search_cache.py','affected_connections.py','rr_batch_occupancy.py','physical_prediction_audit.py','rr_occupancy.py','connection_golden.py','template_connectivity.py','template_sketch.py','pin_pools.py','pin_template_trial.py','prediction_metrics.py','semantic_sketch.py','run_sketch.py']
for n in names:shutil.copyfile(Path(__file__).with_name(n),out/'source'/n)
proto={'scope':'diffeq real two-CLB swap, finite template and cache; no native feedback claim','inputs':{k:{'path':str(p.resolve()),'sha256':sha(p)} for k,p in paths.items()},'refinement_rounds':2,'margin':1,'cache_groups':128,'source_sha256':{n:sha(out/'source'/n) for n in names}}
(out/'protocol.json').write_text(json.dumps(proto,indent=2)+'\n')
g=read_rr_graph(paths['graph']);old=json.loads(paths['old_endpoints'].read_text());candidate=json.loads(paths['old_candidate'].read_text());closure=affected(old,new)
cache=CachedRegionalSearch(g);factory=lambda graph,margin:cache
start=time.monotonic();initial=repair(g,old,candidate,search_type=factory);initialize=time.monotonic()-start
ledger=BatchOccupancy(g)
for r in initial['connections']:
    assert ledger.update(r['connection_id'],1,r['net_id'],r['source'],r['sink'],r['physical_edge_ids'])==Result.COMMITTED
ids=set(closure['recompute_connection_ids']);dirty={**new,'connections':[r for r in new['connections'] if r['connection_id'] in ids]}
hits=cache.hits;misses=cache.misses;start=time.monotonic()
partial_candidate=construct(g,dirty,2);partial=repair(g,dirty,partial_candidate,search_type=factory);partial_wall=time.monotonic()-start
updates=[{**{k:r[k] for k in ('connection_id','net_id','source','sink')},'epoch':2,'edge_ids':r['physical_edge_ids']} for r in partial['connections']]
updates.extend({'connection_id':cid,'epoch':2,'remove':True} for cid in closure['remove_connection_ids'])
assert ledger.update_batch(updates)==Result.COMMITTED
start=time.monotonic();fresh_candidate=construct(g,new,2);fresh=repair(g,new,fresh_candidate,search_type=LazyRegionalSearch);full_wall=time.monotonic()-start
merged={r['connection_id']:r for r in initial['connections']}
for cid in closure['remove_connection_ids']:merged.pop(cid)
for r in partial['connections']:merged[r['connection_id']]=r
fresh_rows={r['connection_id']:r for r in fresh['connections']}
assert json.loads(json.dumps(merged))==json.loads(json.dumps(fresh_rows))
assert {str(n):v for n,v in ledger.occupancy.items() if v}==fresh['node_occupancy']
independent=audit(g,new,{**fresh,'connections':list(merged.values())})
for n,obj in [('partial_candidate',partial_candidate),('partial',partial),('fresh_candidate',fresh_candidate),('fresh',fresh),('closure',closure)]:
    (out/f'{n}.json').write_text(json.dumps(obj,indent=2)+'\n')
result={'protocol_sha256':sha(out/'protocol.json'),'recomputed':len(ids),'requested':len(new['connections']),'exact_paths_methods_and_union':True,'independent_raw_path_audit':independent,'partial_candidate_work':partial_candidate['work'],'partial_repair_work':partial['repair_work'],'full_candidate_work':fresh_candidate['work'],'full_repair_work':fresh['repair_work'],'cache_hits_during_update':cache.hits-hits,'cache_misses_during_update':cache.misses-misses,'initial_repair_wall_s':initialize,'partial_construct_repair_wall_s':partial_wall,'full_construct_repair_wall_s':full_wall,'artifacts':{p.name:sha(p) for p in out.glob('*.json') if p.name!='protocol.json'},'limitations':['index reconstruction included but batch/endpoint/initial-state excluded from update timing','not native routing/placement feedback','single swap/cohort']}
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
