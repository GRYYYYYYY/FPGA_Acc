"""Actual fixed-cost expanded sketch recomputation; no native labels."""
import json,time,shutil
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from prepared_endpoints import PreparedEndpoints
from prepared_templates import PreparedTemplates
from compact_indexed_sketch import CompactIndexedSketch
from regional_search_cache import CachedRegionalSearch
from hybrid_repair import repair
from rr_local_batch_occupancy import LocalBatchOccupancy
from connection_golden import Result
from physical_prediction_audit import audit
from feedback_scores import scores
out=Path('experiments/elliptic_neighborhood_recompute_2026-10-05');parent=Path('experiments/elliptic_sketch_neighborhood_2026-10-05')
if out.exists():raise ValueError('fresh output required')
out.mkdir();(out/'source').mkdir()
for f in Path('tools').glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
epath=Path('experiments/elliptic_endpoints_2026-10-04/endpoints.json');e=json.loads(epath.read_text());place=Path('experiments/elliptic_local_candidates_2026-10-05/candidate_6.place');ppath=Path('experiments/elliptic_prospective_feedback_2026-10-05/candidate_6_prediction.json')
files=[epath,place,ppath,parent/'baseline_prediction.json']+[parent/f'closure_{h}.json' for h in (0,1,2)]
inputs={str(p):sha(p) for p in files};inputs.update({v['path']:v['sha256'] for v in e['inputs'].values()})
assert all(sha(p)==h for p,h in inputs.items())
(out/'protocol.json').write_text(json.dumps({'inputs_sha256':inputs,'hops':[0,1,2],'cost':'unchanged templates refinement2 and regional margin1, independent topology-only search','scope':'development ablation, no candidate native labels','source_sha256':{p.name:sha(p) for p in (out/'source').glob('*.py')}},indent=2)+'\n')
t=time.monotonic();g=read_rr_graph(e['inputs']['graph']['path']);frontend=PreparedEndpoints(e['inputs']['net']['path'],e['inputs']['graph']['path'],e['inputs']['place']['path']);after,_=frontend.project(place);templates=PreparedTemplates(g,2,search_type=CompactIndexedSketch)
baseline=json.loads((parent/'baseline_prediction.json').read_text());reference=json.loads(ppath.read_text());audit(g,e,baseline);audit(g,after,reference);ledger=LocalBatchOccupancy(g)
for r in baseline['connections']:assert ledger.update(r['connection_id'],1,r['net_id'],r['source'],r['sink'],r['physical_edge_ids'])==Result.COMMITTED
old={r['connection_id']:r for r in baseline['connections']};ref={r['connection_id']:r for r in reference['connections']};prep=time.monotonic()-t;reports=[]
for hops in (0,1,2):
 closure=json.loads((parent/f'closure_{hops}.json').read_text());ids=set(closure['recompute_connection_ids']);dirty={**after,'connections':[r for r in after['connections'] if r['connection_id'] in ids]}
 t=time.monotonic();cache=CachedRegionalSearch(g);cache_wall=time.monotonic()-t
 t=time.monotonic();partial=repair(g,dirty,templates.predict(dirty),search_type=lambda graph,margin:cache);search_wall=time.monotonic()-t
 t=time.monotonic();branch=ledger.fork();updates=[{**{k:r[k] for k in ('connection_id','net_id','source','sink')},'epoch':2,'edge_ids':r['physical_edge_ids']} for r in partial['connections']];assert branch.update_batch(updates)==Result.COMMITTED
 merged=dict(old);merged.update({r['connection_id']:r for r in partial['connections']});rows=list(merged.values());p={'physical_graph_sha256':g.sha256,'connections':rows,'node_occupancy':{str(n):v for n,v in branch.occupancy.items() if v},'methods':dict(Counter(r['method'] for r in rows)),'requested':len(rows),'completed':len(rows)};quality=scores(g,after,p['node_occupancy']);commit_score_wall=time.monotonic()-t
 checked=audit(g,after,p);changed=[r['connection_id'] for r in rows if tuple(r['physical_edge_ids'])!=tuple(ref[r['connection_id']]['physical_edge_ids'])]
 (out/f'prediction_{hops}.json').write_text(json.dumps(p)+'\n');report={'hops':hops,'recomputed_connections':len(ids),'fresh_cache_wall_s':cache_wall,'search_wall_s':search_wall,'fork_commit_export_score_wall_s':commit_score_wall,'quality':quality,'path_differences_vs_frozen_candidate':len(changed),'physical_audit':checked};reports.append(report);print(json.dumps(report),flush=True)
assert all(sha(p)==h for p,h in inputs.items())
(out/'receipt.json').write_text(json.dumps({'preparation_wall_s':prep,'reports':reports,'input_hashes_unchanged':True,'limitations':['single development candidate','independent congestion-unaware search','includes fresh cache setup per arm; closure construction archived separately','no native QoR improvement claim']},indent=2)+'\n')
