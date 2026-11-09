"""Maximum ordered pending prefix under witness owner union cap, owner-witness release union, bounded local joint plan."""
import sys,json,time
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from mcnc_bounded_owner_cache_v4 import minimum_witness
from joint_owner_edge_context_v5 import joint_route
from remaining_delay_session_cache_v5 import RemainingDelayCache
parent=R/'experiments/mcnc_bounded_owner_screened_joint_v9_2026-10-07';base=R/'experiments/mcnc_prospective_v1_2026-10-07/dsip';out=R/'experiments/dsip_prefix_edge_context_v7_2026-10-07';out.mkdir();ep=base/'endpoints.json';candidate=parent/'dsip/candidate.json';floorfile=parent/'dsip/floors.json';inputs={str(p):sha(p) for p in (ep,candidate,floorfile,parent/'receipt.json')};inputs.update({v['path']:v['sha256'] for v in json.loads(ep.read_text())['inputs'].values()});sources=closure([Path(__file__)]);(out/'protocol.json').write_text(json.dumps(dict(inputs=inputs,sources=sources,selection='Compute all pending original witnesses; choose maximal ordered prefix whose cumulative blocking owner union<=4; no alternative witness selection. All remaining demand recorded, only selected prefix joint-planned.',max_joint_nodes=64,cache_entries=256,frontier='dfs',memo='In-call fixed-kept/groups/weights/floors/limits context; key NET+forbidden; no reuse between transactions; deadline failures never cached',deadline_seconds=120,limit_change='Post-outcome development continuation evidence: independent fresh run raises joint-node32 to64 and local search60s to120s; not old-config success.',scope='Post-outcome development additional local attempt after 8-batch stop, not original full-cohort success/time or prospective integration. All pending demand/group routing no native labels.'))+'\n');begin=time.perf_counter();graph,digest,nodes,f,rc,queries=load_endpoints(ep);before=json.loads(candidate.read_text());pending=[q for q in sorted(queries,key=lambda q:(q['net_id'],q['connection_id'])) if q['connection_id'] in set(before['pending_connection_ids'])];assert len(pending)==12;floors={(r['source'],r['sink']):r['minimum_integer'] for r in json.loads(floorfile.read_text())};slots={e:s for s,e in enumerate(f['edge_ids'])};owners=defaultdict(set)
for r in before['records']:owners[r['net_id']].add(r['source']);owners[r['net_id']].update(f['dest_ranks'][slots[e]] for e in r['answer']['physical_edge_ids'])
release=set();evidence=[]
for q in pending:
 path=minimum_witness(f,rc,q);assert path is not None;used={q['source']}|{f['dest_ranks'][slots[e]] for e in path};other=Counter(n for net,own in owners.items() if net!=q['net_id'] for n in own);blocked=sorted(n for n in used if other[n]>=f['capacities'][n]);blocking=sorted(net for net,own in owners.items() if net!=q['net_id'] and own.intersection(blocked));release.update(blocking);evidence.append(dict(query=q,physical_edge_ids=path,minimum_integer=rc.path(q['source'],q['sink'],path),blocked_nodes=blocked,blocking_net_ids=blocking))
all_pending=pending;selected=[];prefix_release=set()
for item in evidence:
 expanded=prefix_release|set(item['blocking_net_ids'])
 if len(expanded)>4:break
 selected.append(item['query']);prefix_release=expanded
pending=selected;release=prefix_release
(out/'release_evidence.json').write_text(json.dumps(evidence,indent=2)+'\n');(out/'requested_queries.json').write_text(json.dumps(pending)+'\n');result=None;cache=None
if len(release)<=4:
 kept=[r for r in before['records'] if r['net_id'] not in release];removed=[r for r in before['records'] if r['net_id'] in release];groups=defaultdict(list)
 for q in pending:groups[q['net_id']].append(q)
 for r in sorted(removed,key=lambda r:(r['net_id'],r['connection_id'])):groups[r['net_id']].append({k:r[k] for k in ('connection_id','net_id','source','sink')})
 spans=[1+int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow'))+int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')) if n.get('type') in ('CHANX','CHANY') else 0 for n in nodes];cache=RemainingDelayCache(graph,digest,f,rc,out/'bounds',max_entries=256);start=time.perf_counter()
 def observe(entry,states,solution):
  work=out/f"branch{entry['index']}";work.mkdir();(work/'branch.json').write_text(json.dumps(entry)+'\n')
  for net,state in states.items():(work/f'net{net}.json').write_text(json.dumps(state)+'\n')
  if solution is not None:(work/'joint_candidate.json').write_text(json.dumps(solution)+'\n')
  print(entry['index'],entry['status'],entry.get('conflict_node'),flush=True)
 result=joint_route(cache.fields,cache.rc,dict(groups),floors,kept,spans,rc.scale//10**11,len(queries),remaining_cache=cache,deadline=start+120,max_joint_nodes=64,observer=observe,frontier='dfs',reuse_groups=True);cache.finalize();(out/'cache_receipt.json').write_text(json.dumps(cache.summary(),indent=2)+'\n');(out/'joint_result.json').write_text(json.dumps(result,indent=2)+'\n')
assert all(sha(p)==h for p,h in {**inputs,**sources}.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),released_net_ids=sorted(release),pending_ids=[q['connection_id'] for q in pending],all_pending_ids=[q['connection_id'] for q in all_pending],status='OWNER_LIMIT' if result is None else result['status'],completed=None if result is None or result['solution'] is None else result['solution']['completed_connections'],global_required=len(queries),total_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in out.rglob('*') if p.is_file()}),indent=2)+'\n')
