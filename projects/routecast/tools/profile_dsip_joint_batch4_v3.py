"""Post-outcome CPU profile of one authenticated joint search, without archival observer."""
import sys,json,time,cProfile,pstats
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from remaining_delay_session_cache_v5 import RemainingDelayCache
from joint_owner_seed_context_v7 import joint_route
parent=R/'experiments/mcnc_pending_swap_transactions16_v17_2026-10-07';base=R/'experiments/mcnc_prospective_v1_2026-10-07/dsip';out=R/'experiments/dsip_joint_profile_batch4_v3_2026-10-07';out.mkdir()
receipt=json.loads((parent/'receipt.json').read_text());row=next(r for r in receipt['rows'] if r['name']=='dsip');ep=base/'endpoints.json';bp=parent/'dsip/batch4.json';fp=parent/'dsip/floors.json';assert sha(bp)==row['files'][str(bp)] and sha(fp)==row['files'][str(fp)]
bindings={**closure([Path(__file__)]),str(bp):sha(bp),str(fp):sha(fp),str(ep):sha(ep),str(parent/'receipt.json'):sha(parent/'receipt.json')};bindings.update({v['path']:v['sha256'] for v in json.loads(ep.read_text())['inputs'].values()})
assert all(sha(k)==v for k,v in bindings.items());(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Authenticated dsip batch4 replay, sameDFS64 objective and group order, fresh FIFO256 cache. No archival observer, profile overhead paid and no deadline to obtain full bounded trace. Post-outcome component diagnostic, not live/end-to-end timing, unseen-family evidence or gain.'),indent=2)+'\n')
graph,digest,nodes,f,rc,queries=load_endpoints(ep);floors={(r['source'],r['sink']):r['minimum_integer'] for r in json.loads(fp.read_text())};event=json.loads(bp.read_text());release=set(event['initial_release_net_ids']);kept=[r for r in event['before_records'] if r['net_id'] not in release];removed=[r for r in event['before_records'] if r['net_id'] in release];groups=defaultdict(list)
for q in event['selection']['queries']:groups[q['net_id']].append(q)
for r in sorted(removed,key=lambda r:(r['net_id'],r['connection_id'])):groups[r['net_id']].append({k:r[k] for k in ('connection_id','net_id','source','sink')})
spans=[1+int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow'))+int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')) if n.get('type') in ('CHANX','CHANY') else 0 for n in nodes];assert rc.scale%10**11==0;cache=RemainingDelayCache(graph,digest,f,rc,out/'bounds',max_entries=256)
pr=cProfile.Profile();start=time.perf_counter();pr.enable();result=joint_route(cache.fields,cache.rc,dict(groups),floors,kept,spans,4*(rc.scale//10**11),len(queries),remaining_cache=cache,max_joint_nodes=64,frontier='dfs',reuse_groups=True);pr.disable();elapsed=time.perf_counter()-start;cache.finalize();pr.dump_stats(str(out/'profile.pstats'))
assert json.loads(json.dumps(result['branches']))==event['repair_attempts'] and result['solution']['records']==event['working_records']
(out/'result.json').write_text(json.dumps(result)+'\n')
with (out/'profile_cumulative.txt').open('w') as stream:pstats.Stats(pr,stream=stream).strip_dirs().sort_stats('cumulative').print_stats(40)
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),profiled_joint_seconds=elapsed,exact_reference_branches_and_records=True,branches=len(result['branches']),low_level_requests=result['low_level_requests'],low_level_computations=result['low_level_computations'],files={str(p):sha(p) for p in out.rglob('*') if p.is_file()}),indent=2)+'\n');print('PASS profile exact branch/record replay',elapsed,flush=True)
