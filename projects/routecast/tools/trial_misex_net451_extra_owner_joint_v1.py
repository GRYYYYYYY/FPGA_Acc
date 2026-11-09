"""Extra-owner saved failure reinsert trial: every selected and released NET retained."""
import sys,json,time
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from remaining_delay_worker_cache_v7 import RemainingDelayCache
from joint_owner_observer_clone_v9 import joint_route
parent=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07';proposal=R/'experiments/misex_net451_failure_owner_domains_v1_2026-10-07';out=R/'experiments/misex_net451_extra_owner_joint_v1_2026-10-07';out.mkdir();rp=proposal/'receipt.json';pr=json.loads(rp.read_text());vp=proposal/'positive_witness_verification.json';vr=json.loads(vp.read_text());assert vr['positive_witnesses_verified']>0;assert all(sha(k)==h for k,h in vr['bindings'].items());assert all(sha(k)==h for k,h in pr['bindings'].items());ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';bp=parent/'misex3/batch14.json';fp=parent/'misex3/floors.json';binary=R/'build/capped_bound_worker_cpp_v2_2026-10-07/compute';cpp=R/'tools/capped_bound_worker_cpp_v2/main.cpp';bindings={**pr['bindings'],**closure([Path(__file__)]),str(rp):sha(rp),str(vp):sha(vp),str(binary):sha(binary),str(cpp):sha(cpp)};(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,policy=dict(max_candidate_attempts=8,max_joint_nodes=64,frontier='dfs',owner_limit=7,deadline_seconds=120,selected='All frozen pending requests plus every complete released NET including added owner; groups CID ordered'),scope='Post-outcome snapshot component, paid worker construction/search/observer/finalize, original cohort not rerun. Post-outcome failure screening previously paid/reported separately; extra-owner work is not a matched-work ablation; all new attempts included. No heldout/full native/cold workflow gain.'),indent=2)+'\n');begin=time.perf_counter();graph,digest,nodes,f,rc,queries=load_endpoints(ep);event=json.loads((R/'experiments/misex_window_witness_guided_joint_v29_2026-10-07/event.json').read_text());(out/'event.json').write_text(json.dumps(event)+'\n');floors={(d['source'],d['sink']):d['minimum_integer'] for d in json.loads(fp.read_text())};spans=[1+int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow'))+int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')) if n.get('type') in ('CHANX','CHANY') else 0 for n in nodes];cache=RemainingDelayCache(graph,digest,f,rc,out/'bounds',max_entries=256);counts=defaultdict(int)
for rec in event['before_records']:counts[rec['net_id']]+=1
coverage=defaultdict(set)
for row in pr['rows']:
 for check in row['checks']:
  if check['witness'] is not None:coverage[tuple(sorted(set(row['release'])|{check['extra_net']}))].add(row['query']['connection_id'])
coverage={ns:cids for ns,cids in coverage.items() if len(ns)<=7};ordered=sorted(coverage,key=lambda release:(-len(coverage[release]),sum(counts[net] for net in release),release))[:8];proposed=[list(release) for release in ordered];(out/'candidates.json').write_text(json.dumps([dict(release=list(release),restored_failed_connection_ids=sorted(coverage[release])) for release in ordered],indent=2)+'\n');start=time.perf_counter();attempts=[];solution=None
try:
 for index,release in enumerate(proposed):
  assert 1<=len(release)<=7;removed=[r for r in event['before_records'] if r['net_id'] in release];kept=[r for r in event['before_records'] if r['net_id'] not in release];groups=defaultdict(list)
  for q in event['selection']['queries']:groups[q['net_id']].append(q)
  for rec in sorted(removed,key=lambda r:(r['net_id'],r['connection_id'])):groups[rec['net_id']].append({k:rec[k] for k in ('connection_id','net_id','source','sink')})
  groups={net:sorted(qs,key=lambda q:q['connection_id']) for net,qs in groups.items()}
  def observe(branch,states,merged):
   directory=out/f"attempt{index}_branch{branch['index']}";directory.mkdir();(directory/'branch.json').write_text(json.dumps(dict(released_net_ids=release,branch=branch))+'\n')
   for net,state in states.items():(directory/f'net{net}.json').write_text(json.dumps(state)+'\n')
   if merged is not None:(directory/'joint_candidate.json').write_text(json.dumps(merged)+'\n')
  result=joint_route(cache.fields,cache.rc,dict(groups),floors,kept,spans,4*(rc.scale//10**11),len(queries),remaining_cache=cache,max_joint_nodes=64,deadline=start+120,observer=observe,frontier='dfs',reuse_groups=True);attempts.append(dict(index=index,release=release,status=result['status'],branches=result['branches'],removed_connection_ids=[r['connection_id'] for r in removed]));print(index,release,result['status'],len(result['branches']),flush=True)
  if result['solution'] is not None:
   solution=result['solution'];assert {r['connection_id'] for r in solution['records']}=={r['connection_id'] for r in event['before_records']}|set(event['selection']['requested_connection_ids']);break
  if result['status']=='DEADLINE':break
 cache.finalize()
finally:
 if not cache._closed:cache.abort()
(out/'candidate.json').write_text(json.dumps(solution)+'\n');(out/'cache_receipt.json').write_text(json.dumps(cache.summary(),indent=2)+'\n');assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),attempts=attempts,completed=None if solution is None else solution['completed_connections'],required=len(queries),search_and_finalize_seconds=time.perf_counter()-start,total_component_seconds=time.perf_counter()-begin,bindings=bindings,files={str(p):sha(p) for p in out.rglob('*') if p.is_file()}),indent=2)+'\n')
