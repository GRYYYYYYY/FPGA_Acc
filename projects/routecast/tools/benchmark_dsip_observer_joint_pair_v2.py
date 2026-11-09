"""Post-outcome CPU profile of one authenticated joint search, without archival observer."""
import sys,json,time,statistics
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from remaining_delay_worker_cache_v7 import RemainingDelayCache
from joint_owner_seed_context_v7 import joint_route as old_joint
from joint_owner_observer_clone_v9 import joint_route as new_joint
parent=R/'experiments/mcnc_pending_swap_transactions16_v17_2026-10-07';base=R/'experiments/mcnc_prospective_v1_2026-10-07/dsip';out=R/'experiments/dsip_observer_joint_pair_v2_2026-10-07';out.mkdir()
receipt=json.loads((parent/'receipt.json').read_text());row=next(r for r in receipt['rows'] if r['name']=='dsip');ep=base/'endpoints.json';bp=parent/'dsip/batch4.json';fp=parent/'dsip/floors.json';assert sha(bp)==row['files'][str(bp)] and sha(fp)==row['files'][str(fp)]
bindings={**closure([Path(__file__)]),str(bp):sha(bp),str(fp):sha(fp),str(ep):sha(ep),str(parent/'receipt.json'):sha(parent/'receipt.json')};bindings.update({v['path']:v['sha256'] for v in json.loads(ep.read_text())['inputs'].values()})
for artifact in (R/'build/capped_bound_worker_cpp_v2_2026-10-07/compute',R/'tools/capped_bound_worker_cpp_v2/main.cpp'):
 bindings[str(artifact)]=sha(artifact)
reference=parent/'dsip'
reference_files=sorted(reference.glob('repair_batch4_attempt1_branch*/*.json'))
for file in reference_files:assert sha(file)==row['files'][str(file)];bindings[str(file)]=sha(file)
assert all(sha(k)==v for k,v in bindings.items());(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Authenticated dsip batch4 replay, sameDFS64 objective and group order, fresh FIFO256 cache. Four alternating old/new pairs; same fresh on-demand worker FIFO256 cache, original archival observer writes; observer cloning sole change. Constructor separately paid plusjoint/archive/finalize. No profile/no deadline, obtains full DFS64 trace. Reference parity outside timing. Post-outcome component diagnostic, not live/end-to-end timing, unseen-family evidence or gain.'),indent=2)+'\n')
graph,digest,nodes,f,rc,queries=load_endpoints(ep);floors={(r['source'],r['sink']):r['minimum_integer'] for r in json.loads(fp.read_text())};event=json.loads(bp.read_text());release=set(event['initial_release_net_ids']);kept=[r for r in event['before_records'] if r['net_id'] not in release];removed=[r for r in event['before_records'] if r['net_id'] in release];groups=defaultdict(list)
for q in event['selection']['queries']:groups[q['net_id']].append(q)
for r in sorted(removed,key=lambda r:(r['net_id'],r['connection_id'])):groups[r['net_id']].append({k:r[k] for k in ('connection_id','net_id','source','sink')})
spans=[1+int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow'))+int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')) if n.get('type') in ('CHANX','CHANY') else 0 for n in nodes];assert rc.scale%10**11==0
rows=[]
for repeat in range(4):
 for name,fn in ([('old',old_joint),('new',new_joint)] if repeat%2==0 else [('new',new_joint),('old',old_joint)]):
  work=out/f'{repeat}_{name}';work.mkdir();cache=RemainingDelayCache(graph,digest,f,rc,work/'bounds',max_entries=256)
  def observe(branch,states,solution):
   directory=work/f"repair_batch4_attempt1_branch{branch['index']}";directory.mkdir();(directory/'branch.json').write_text(json.dumps(dict(released_net_ids=event['initial_release_net_ids'],branch=branch))+'\n')
   for net,state in states.items():(directory/f'net{net}.json').write_text(json.dumps(state)+'\n')
   if solution is not None:(directory/'joint_candidate.json').write_text(json.dumps(solution)+'\n')
  start=time.perf_counter()
  try:
   result=fn(cache.fields,cache.rc,dict(groups),floors,kept,spans,4*(rc.scale//10**11),len(queries),remaining_cache=cache,max_joint_nodes=64,frontier='dfs',reuse_groups=True,observer=observe);cache.finalize()
  finally:
   if not cache._closed:cache.abort()
  elapsed=time.perf_counter()-start
  assert json.loads(json.dumps(result['branches']))==event['repair_attempts'] and result['solution']['records']==event['working_records']
  for file in reference_files:assert (work/file.parent.name/file.name).read_bytes()==file.read_bytes()
  generated=sorted(work.glob('repair_batch4_attempt1_branch*/*.json'));assert len(generated)==len(reference_files)
  (work/'result.json').write_text(json.dumps(result)+'\n');(work/'cache_receipt.json').write_text(json.dumps(cache.summary(),indent=2)+'\n')
  rows.append(dict(repeat=repeat,version=name,joint_archive_and_finalize_seconds=elapsed,construction_seconds=cache.construction_seconds,total_paid_component_seconds=elapsed+cache.construction_seconds,branches=len(result['branches']),archived_files=len(generated),all_reference_archive_bytes_equal=True));print(rows[-1],flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows,median_total_paid_seconds={n:statistics.median(r['total_paid_component_seconds'] for r in rows if r['version']==n) for n in ('old','new')},bindings=bindings,files={str(p):sha(p) for p in out.rglob('*') if p.is_file()}),indent=2)+'\n')
