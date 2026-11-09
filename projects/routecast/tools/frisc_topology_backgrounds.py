"""Frozen prospective topology backgrounds; no candidate native route reads."""
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
from affected_connections import affected
from rr_local_batch_occupancy import LocalBatchOccupancy
from connection_golden import Result
from physical_prediction_audit import audit
from feedback_scores import scores
out=Path('experiments/frisc_topology_backgrounds_2026-10-05');epath=Path('experiments/frisc_endpoints_2026-10-05/endpoints.json');parent=Path('experiments/frisc_local_candidates_2026-10-05')
if out.exists():raise ValueError('fresh output required')
out.mkdir();(out/'source').mkdir()
for f in Path('tools').glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
e=json.loads(epath.read_text());inputs={str(epath):sha(epath),str(parent/'receipt.json'):sha(parent/'receipt.json'),**{v['path']:v['sha256'] for v in e['inputs'].values()},**{str(parent/f'candidate_{c}.place'):sha(parent/f'candidate_{c}.place') for c in range(1,9)}}
assert all(sha(p)==h for p,h in inputs.items())
(out/'protocol.json').write_text(json.dumps({'inputs_sha256':inputs,'prospective_protocol_sha256':sha('experiments/frisc_prospective_protocol_2026-10-05/protocol.json'),'refinement':2,'margin':1,'source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')},'scope':'same frozen topology method, original baseline and8 candidate backgrounds, no candidate native labels'},indent=2)+'\n')
start=time.monotonic();g=read_rr_graph(e['inputs']['graph']['path']);frontend=PreparedEndpoints(e['inputs']['net']['path'],e['inputs']['graph']['path'],e['inputs']['place']['path']);templates=PreparedTemplates(g,2,search_type=CompactIndexedSketch);cache=CachedRegionalSearch(g);factory=lambda graph,margin:cache
baseline=repair(g,e,templates.predict(e),search_type=factory);audit(g,e,baseline);(out/'baseline_prediction.json').write_text(json.dumps(baseline)+'\n');ledger=LocalBatchOccupancy(g)
for r in baseline['connections']:assert ledger.update(r['connection_id'],1,r['net_id'],r['source'],r['sink'],r['physical_edge_ids'])==Result.COMMITTED
prep=time.monotonic()-start;old={r['connection_id']:r for r in baseline['connections']};rows=[{'candidate_id':0,'scores':scores(g,e,baseline['node_occupancy'])}];print(json.dumps({'baseline_preparation_wall_s':prep}),flush=True)
for cid in range(1,9):
 t=time.monotonic();after,_=frontend.project(parent/f'candidate_{cid}.place');closure=affected(e,after);ids=set(closure['recompute_connection_ids']);dirty={**after,'connections':[r for r in after['connections'] if r['connection_id'] in ids]};partial=repair(g,dirty,templates.predict(dirty),search_type=factory);branch=ledger.fork()
 assert branch.update_batch([{**{k:r[k] for k in ('connection_id','net_id','source','sink')},'epoch':2,'edge_ids':r['physical_edge_ids']} for r in partial['connections']])==Result.COMMITTED
 merged=dict(old);merged.update({r['connection_id']:r for r in partial['connections']});connections=list(merged.values());p={'physical_graph_sha256':g.sha256,'connections':connections,'node_occupancy':{str(n):v for n,v in branch.occupancy.items() if v},'methods':dict(Counter(r['method'] for r in connections)),'requested':len(connections),'completed':len(connections)};checked=audit(g,after,p)
 (out/f'candidate_{cid}_prediction.json').write_text(json.dumps(p)+'\n');row={'candidate_id':cid,'wall_s':time.monotonic()-t,'scores':scores(g,after,p['node_occupancy']),'recomputed_connections':len(ids),'physical_audit':checked};rows.append(row);print(json.dumps(row),flush=True)
assert all(sha(p)==h for p,h in inputs.items())
(out/'receipt.json').write_text(json.dumps({'preparation_wall_s':prep,'full_wall_s':time.monotonic()-start,'rows':rows,'inputs_unchanged':True,'limitations':['no candidate native QoR assessed','same architecture additional design','physical paths not joint-tree legality']},indent=2)+'\n')
