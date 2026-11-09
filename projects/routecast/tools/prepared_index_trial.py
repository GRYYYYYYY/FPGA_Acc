"""Warm prepared-template queries on unchanged matched-HPWL artifacts."""
import json,shutil,time
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from prepared_templates import PreparedTemplates
from hybrid_repair import repair
from regional_search_cache import CachedRegionalSearch
from affected_connections import affected
from physical_prediction_audit import audit
from feedback_scores import scores

out=Path('experiments/prepared_index_2026-10-04')
if out.exists():raise ValueError('fresh output required')
out.mkdir();(out/'source').mkdir();prior=Path('experiments/matched_hpwl_trial_2026-10-04');base=Path('experiments/pre_route_endpoints_2026-10-04/diffeq_endpoints.json');ep=json.loads(base.read_text());graph=Path(ep['inputs']['graph']['path'])
modules=['prepared_index_trial.py','prepared_templates.py','pre_route_endpoints.py','rr_graph.py','hybrid_repair.py','regional_search_cache.py','lazy_region_search.py','affected_connections.py','physical_prediction_audit.py','feedback_scores.py','rr_occupancy.py','connection_golden.py','template_connectivity.py','template_sketch.py','pin_pools.py','semantic_sketch.py']
for name in modules:shutil.copyfile(Path(__file__).with_name(name),out/'source'/name)
inputs={'graph':graph,'baseline':base}
for cid in range(1,8):
    inputs[f'ep_{cid}']=prior/f'candidate_{cid}_endpoints.json';inputs[f'full_{cid}']=prior/f'candidate_{cid}_prediction.json'
p={'scope':'same seven existing matched-HPWL inputs, graph/index reuse only; unchanged algorithm and scores','inputs':{k:{'path':str(v.resolve()),'sha256':sha(v)} for k,v in inputs.items()},'refinement_rounds':2,'margin':1,'cache_groups':128,'query_timing':'closure + partial prediction/repair + physical union merge + score; excludes JSON load, shared initialization and independent audit','source_sha256':{n:sha(out/'source'/n) for n in modules}}
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');started=time.monotonic();g=read_rr_graph(graph);graph_wall=time.monotonic()-started
started=time.monotonic();prepared=PreparedTemplates(g,2);cache=CachedRegionalSearch(g);factory=lambda graph,margin:cache;initial=repair(g,ep,prepared.predict(ep),search_type=factory);initialization=time.monotonic()-started
old={r['connection_id']:r for r in initial['connections']};reports=[]
for cid in range(1,8):
    load=time.monotonic();after=json.loads(inputs[f'ep_{cid}'].read_text());fresh=json.loads(inputs[f'full_{cid}'].read_text());input_wall=time.monotonic()-load
    started=time.monotonic();closure=affected(ep,after);ids=set(closure['recompute_connection_ids']);dirty={**after,'connections':[r for r in after['connections'] if r['connection_id'] in ids]}
    hits,misses=cache.hits,cache.misses;candidate=prepared.predict(dirty);partial=repair(g,dirty,candidate,search_type=factory);merged=dict(old)
    for r in partial['connections']:merged[r['connection_id']]=r
    users={}
    for r in merged.values():
        nodes={r['source']}|{g.edges[eid].sink for eid in r['physical_edge_ids']}
        for n in nodes:users.setdefault(n,set()).add(r['net_id'])
    occupancy={str(n):len(v) for n,v in users.items()};quality=scores(g,after,occupancy);wall=time.monotonic()-started
    assert json.loads(json.dumps(merged))==json.loads(json.dumps({r['connection_id']:r for r in fresh['connections']}))
    assert occupancy==fresh['node_occupancy'];checked=audit(g,after,{**fresh,'connections':list(merged.values())})
    r={'candidate_id':cid,'recomputed':len(ids),'query_wall_s':wall,'json_input_wall_s':input_wall,'cache_hits':cache.hits-hits,'cache_misses':cache.misses-misses,'candidate_work':candidate['work'],'repair_work':partial['repair_work'],'scores':quality,'exact_archived_full_paths_methods_union':True,'independent_audit':checked}
    reports.append(r);print(json.dumps(r),flush=True)
for v in p['inputs'].values():
    assert sha(v['path'])==v['sha256']
result={'protocol_sha256':sha(out/'protocol.json'),'graph_load_wall_s':graph_wall,'shared_preparation_and_baseline_wall_s':initialization,'total_query_wall_s':sum(r['query_wall_s'] for r in reports),'total_json_input_wall_s':sum(r['json_input_wall_s'] for r in reports),'reports':reports,'limitations':['endpoint conversion remains outside queries','batch commit not modeled here','shared initialization not free','same candidates/outcomes; no new optimization quality','CPU exploration only']}
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
