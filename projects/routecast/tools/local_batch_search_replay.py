"""Real endpoint conversion, affected search and local-ledger commit replay."""
import json,shutil,time
from pathlib import Path
from pre_route_endpoints import sha, extract
from rr_local_batch_occupancy import LocalBatchOccupancy
from connection_golden import Result
from rr_graph import read_rr_graph
from prepared_templates import PreparedTemplates
from compact_indexed_sketch import CompactIndexedSketch
from hybrid_repair import repair
from regional_search_cache import CachedRegionalSearch
from affected_connections import affected
from physical_prediction_audit import audit
from feedback_scores import scores

out=Path('experiments/local_batch_search_replay_2026-10-05')
if out.exists():raise ValueError('fresh output required')
out.mkdir();(out/'source').mkdir();prior=Path('experiments/matched_hpwl_trial_2026-10-04');base=Path('experiments/pre_route_endpoints_2026-10-04/diffeq_endpoints.json');ep=json.loads(base.read_text());graph=Path(ep['inputs']['graph']['path'])
modules=[f.name for f in Path(__file__).parent.glob('*.py')]
for name in modules:shutil.copyfile(Path(__file__).with_name(name),out/'source'/name)
inputs={'graph':graph,'baseline':base,'net':Path(ep['inputs']['net']['path'])}
for cid in range(1,8):
    inputs[f'place_{cid}']=prior/f'candidate_{cid}.place';inputs[f'ep_{cid}']=prior/f'candidate_{cid}_endpoints.json';inputs[f'full_{cid}']=prior/f'candidate_{cid}_prediction.json'
p={'scope':'same seven existing matched-HPWL inputs, indexed outgoing-arc implementation; unchanged paths, counters and scores','inputs':{k:{'path':str(v.resolve()),'sha256':sha(v)} for k,v in inputs.items()},'refinement_rounds':2,'margin':1,'cache_groups':128,'query_timing':'closure + partial search + full fork + local commit + full occupancy export + score; conversion separately measured and included in conversion_plus_query_s; JSON load, shared initialization and validation separately reported','source_sha256':{n:sha(out/'source'/n) for n in modules}}
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');started=time.monotonic();g=read_rr_graph(graph);graph_wall=time.monotonic()-started
started=time.monotonic();prepared=PreparedTemplates(g,2,search_type=CompactIndexedSketch);cache=CachedRegionalSearch(g);factory=lambda graph,margin:cache;initial=repair(g,ep,prepared.predict(ep),search_type=factory);initialization=time.monotonic()-started
old={r['connection_id']:r for r in initial['connections']};reports=[]
ledger=LocalBatchOccupancy(g);start=time.monotonic()
assert ledger.update_batch([{k:r[k] for k in ('connection_id','net_id','source','sink')}|{'epoch':1,'edge_ids':r['physical_edge_ids']} for r in initial['connections']])==Result.COMMITTED
ledger_initialization_s=time.monotonic()-start
for cid in range(1,8):
    load=time.monotonic();after=json.loads(inputs[f'ep_{cid}'].read_text());fresh=json.loads(inputs[f'full_{cid}'].read_text());input_wall=time.monotonic()-load
    started=time.monotonic();converted,_=extract(inputs['net'],inputs[f'place_{cid}'],graph);conversion_s=time.monotonic()-started
    assert converted['connections']==after['connections'] and converted['graph_sha256']==after['graph_sha256']
    started=time.monotonic();closure=affected(ep,after);ids=set(closure['recompute_connection_ids']);dirty={**after,'connections':[r for r in after['connections'] if r['connection_id'] in ids]}
    hits,misses=cache.hits,cache.misses;candidate=prepared.predict(dirty);partial=repair(g,dirty,candidate,search_type=factory);merged=dict(old)
    for r in partial['connections']:merged[r['connection_id']]=r
    fork_start=time.monotonic();branch=ledger.fork();fork_s=time.monotonic()-fork_start
    updates=[{k:r[k] for k in ('connection_id','net_id','source','sink')}|{'epoch':2,'edge_ids':r['physical_edge_ids']} for r in partial['connections']]
    updates.extend({'connection_id':c,'epoch':2,'remove':True} for c in closure['remove_connection_ids'])
    commit_start=time.monotonic()
    if updates:assert branch.update_batch(updates)==Result.COMMITTED
    commit_s=time.monotonic()-commit_start
    occupancy={str(n):v for n,v in branch.occupancy.items() if v};quality=scores(g,after,occupancy);wall=time.monotonic()-started
    assert json.loads(json.dumps(merged))==json.loads(json.dumps({r['connection_id']:r for r in fresh['connections']}))
    assert occupancy==fresh['node_occupancy'];checked=audit(g,after,{**fresh,'connections':list(merged.values())})
    r={'candidate_id':cid,'recomputed':len(ids),'query_wall_s':wall,'conversion_s':conversion_s,'conversion_plus_query_s':conversion_s+wall,'fork_s':fork_s,'commit_s':commit_s,'json_input_wall_s':input_wall,'cache_hits':cache.hits-hits,'cache_misses':cache.misses-misses,'candidate_work':candidate['work'],'repair_work':partial['repair_work'],'scores':quality,'exact_archived_full_paths_methods_union':True,'independent_audit':checked}
    reports.append(r);print(json.dumps(r),flush=True)
for v in p['inputs'].values():
    assert sha(v['path'])==v['sha256']
result={'protocol_sha256':sha(out/'protocol.json'),'graph_load_wall_s':graph_wall,'ledger_initialization_s':ledger_initialization_s,'shared_preparation_and_baseline_wall_s':initialization,'total_query_wall_s':sum(r['query_wall_s'] for r in reports),'total_json_input_wall_s':sum(r['json_input_wall_s'] for r in reports),'reports':reports,'limitations':['conversion and commit included explicitly; native routing remains outside','fork and full occupancy export included in query','shared initialization not free','same candidates/outcomes; no new optimization quality','CPU exploration only']}
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
