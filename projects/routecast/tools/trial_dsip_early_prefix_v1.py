"""Generic pending-prefix selector applied before original eighth transaction."""
import sys,json,time
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from pending_owner_prefix_v1 import select
from joint_owner_constraints_memo_v3 import joint_route
from remaining_delay_session_cache_v5 import RemainingDelayCache
base=R/'experiments/mcnc_prospective_v1_2026-10-07/dsip';parent=R/'experiments/mcnc_bounded_owner_screened_joint_v9_2026-10-07';out=R/'experiments/dsip_early_prefix_v1_2026-10-07';out.mkdir();ep=base/'endpoints.json';eventfile=parent/'dsip/batch8.json';floorfile=parent/'dsip/floors.json';inputs={str(p):sha(p) for p in (ep,eventfile,floorfile,parent/'receipt.json')};inputs.update({v['path']:v['sha256'] for v in json.loads(ep.read_text())['inputs'].values()});sources=closure([Path(__file__)]);(out/'protocol.json').write_text(json.dumps(dict(inputs=inputs,sources=sources,policy='Apply generic ordered pending selector at frozen before-batch8 snapshot; max16queries/max4whole-owner union; joint DFS64 with call-local memo/FIFO256/search120s.',scope='Post-outcome development early-transaction component, not fresh complete-cohort or original 8-batch success/timing. No prepared tail joint or native labels as producer input.'))+'\n');begin=time.perf_counter();graph,digest,nodes,f,rc,queries=load_endpoints(ep);event=json.loads(eventfile.read_text());before=event['before_records'];done={r['connection_id'] for r in before};pending=[q for q in queries if q['connection_id'] not in done];selection=select(f,rc,before,pending,max_owner_nets=4,max_queries=16);(out/'selection.json').write_text(json.dumps(selection,indent=2)+'\n');print('selected',selection['requested_connection_ids'],'release',selection['released_net_ids'],flush=True);release=set(selection['released_net_ids']);kept=[r for r in before if r['net_id'] not in release];removed=[r for r in before if r['net_id'] in release];groups=defaultdict(list)
for q in selection['queries']:groups[q['net_id']].append(q)
for r in sorted(removed,key=lambda r:(r['net_id'],r['connection_id'])):groups[r['net_id']].append({k:r[k] for k in ('connection_id','net_id','source','sink')})
floors={(r['source'],r['sink']):r['minimum_integer'] for r in json.loads(floorfile.read_text())};spans=[1+int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow'))+int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')) if n.get('type') in ('CHANX','CHANY') else 0 for n in nodes];cache=RemainingDelayCache(graph,digest,f,rc,out/'bounds',max_entries=256);start=time.perf_counter()
def observe(entry,states,solution):
 work=out/f"branch{entry['index']}";work.mkdir();(work/'branch.json').write_text(json.dumps(entry)+'\n')
 for net,state in states.items():(work/f'net{net}.json').write_text(json.dumps(state)+'\n')
 if solution is not None:(work/'joint_candidate.json').write_text(json.dumps(solution)+'\n')
 print(entry['index'],entry['status'],entry.get('conflict_node'),flush=True)
result=joint_route(cache.fields,cache.rc,dict(groups),floors,kept,spans,rc.scale//10**11,len(queries),remaining_cache=cache,max_joint_nodes=64,deadline=start+120,observer=observe,frontier='dfs',reuse_groups=True);cache.finalize();(out/'joint_result.json').write_text(json.dumps(result,indent=2)+'\n');(out/'cache_receipt.json').write_text(json.dumps(cache.summary(),indent=2)+'\n');assert all(sha(p)==h for p,h in {**inputs,**sources}.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),status=result['status'],before_completed=len(before),requested_ids=selection['requested_connection_ids'],released_net_ids=sorted(release),removed_ids=[r['connection_id'] for r in removed],completed=None if result['solution'] is None else result['solution']['completed_connections'],global_required=len(queries),total_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in out.rglob('*') if p.is_file()}),indent=2)+'\n')
