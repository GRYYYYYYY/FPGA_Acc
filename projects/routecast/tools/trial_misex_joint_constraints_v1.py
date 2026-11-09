"""Bounded conflict branching over two whole-NET groups, fixed external owners."""
import sys,json,time
from pathlib import Path
from collections import Counter,defaultdict,deque
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from remaining_delay_session_cache_v5 import RemainingDelayCache
from tree_floor_pareto_constraints_predictor_v7 import predict
base=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3';parent=R/'experiments/mcnc_bounded_owner_session_cache_v7_2026-10-07';out=R/'experiments/misex_joint_constraints_v1_2026-10-07';out.mkdir();ep=base/'endpoints.json';eventfile=parent/'misex3/batch5.json';floorfile=parent/'misex3/floors.json';inputs={str(p):sha(p) for p in (ep,eventfile,floorfile,parent/'receipt.json')};inputs.update({v['path']:v['sha256'] for v in json.loads(ep.read_text())['inputs'].values()});sources=closure([Path(__file__)]);protocol=dict(inputs=inputs,sources=sources,max_joint_nodes=32,deadline_seconds=60,policy='BFS; independent whole-group routing against same immutable kept owners; split first capacity conflict rank into prohibit-node NET138 vs NET221. Original budgets/weight/10000 labels/0.5ns lower bounds. No native labels. Preserve every branch and failures.',scope='Development local coupled search; limited branch search not complete solver; no global/native/net-gain claim.');(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');tick=time.perf_counter();graph,digest,nodes,f,rc,_=load_endpoints(ep);event=json.loads(eventfile.read_text());release=set(event['released_net_ids']);kept=[r for r in event['before_records'] if r['net_id'] not in release];removed=sorted((r for r in event['before_records'] if r['net_id'] in release),key=lambda r:r['connection_id']);groups={138:[{k:r[k] for k in ('connection_id','net_id','source','sink')} for r in removed],221:[event['query']]};assert set(release)=={138} and event['query']['net_id']==221;floors={(r['source'],r['sink']):r['minimum_integer'] for r in json.loads(floorfile.read_text())};spans=[1+int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow'))+int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')) if n.get('type') in ('CHANX','CHANY') else 0 for n in nodes];cache=RemainingDelayCache(graph,digest,f,rc,out/'bounds');f=cache.fields;rc=cache.rc;slots={e:s for s,e in enumerate(f['edge_ids'])};queue=deque([frozenset()]);seen={frozenset()};branches=[];solution=None;deadline=time.perf_counter()+60
while queue and len(branches)<32 and time.perf_counter()<deadline:
 constraints=queue.popleft();index=len(branches);work=out/f'branch{index}';work.mkdir();states={};failed=False
 for net in (138,221):
  state=predict(f,rc,groups[net],floors,seed_records=kept,spans=spans,penalty=rc.scale//10**11,remaining_cache=cache,forbidden_by_net={net:frozenset(n for owner,n in constraints if owner==net)},deadline=deadline);states[net]=state;(work/f'net{net}.json').write_text(json.dumps(state)+'\n');failed|=state['failure'] is not None
 entry=dict(index=index,constraints=sorted(constraints),failures={str(k):v['failure'] for k,v in states.items()})
 if failed:entry['status']='LOW_LEVEL_FAILED'
 else:
  records={r['connection_id']:r for r in kept}
  for state in states.values():
   for r in state['records']:
    if r['connection_id'] in records:assert records[r['connection_id']]==r
    records[r['connection_id']]=r
  owners=defaultdict(set)
  for r in records.values():owners[r['net_id']].add(r['source']);owners[r['net_id']].update(f['dest_ranks'][slots[e]] for e in r['answer']['physical_edge_ids'])
  ledger=Counter(n for own in owners.values() for n in own);conflicts=sorted(n for n,v in ledger.items() if v>f['capacities'][n]);entry['conflict_count']=len(conflicts)
  if not conflicts:
   solution=dict(records=sorted(records.values(),key=lambda r:r['connection_id']),ledger=dict(ledger),completed_connections=len(records),required_connections=2449,failure=None,scope='LOCAL_JOINT_BATCH_ONLY_GLOBAL_PARTIAL');entry['status']='FOUND_JOINT_BATCH';(work/'joint_candidate.json').write_text(json.dumps(solution)+'\n')
  else:
   node=conflicts[0];participants=[net for net in (138,221) if node in owners[net]];assert len(participants)==2;entry.update(status='SPLIT',conflict_node=node)
   for net in participants:
    child=constraints|{(net,node)}
    if child not in seen:seen.add(child);queue.append(child)
 branches.append(entry);(out/'branches.json').write_text(json.dumps(branches,indent=2)+'\n');print(index,entry['status'],entry.get('conflict_node'),flush=True)
 if solution is not None:break
cache.finalize();(out/'cache_receipt.json').write_text(json.dumps(cache.summary(),indent=2)+'\n');assert all(sha(p)==h for p,h in {**inputs,**sources}.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),total_seconds=time.perf_counter()-tick,branches=branches,joint_success=solution is not None,global_completed=None if solution is None else solution['completed_connections'],global_required=2449,remaining_branches=len(queue),files={str(p):sha(p) for p in out.rglob('*') if p.is_file()}),indent=2)+'\n')
