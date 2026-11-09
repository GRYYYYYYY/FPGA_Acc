"""Bounded component swap proposals; ordinary witnesses are heuristic, not joint proof."""
import sys,json,time
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from remaining_delay_session_cache_v5 import RemainingDelayCache
from budget_owner_screen_v2 import screen,witness_in_domain
from joint_owner_seed_context_v7 import joint_route
base=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3';parent=R/'experiments/mcnc_pending_expansion_v15_2026-10-07/misex3';out=R/'experiments/misex_owner_swap_v1_2026-10-07';out.mkdir();ep=base/'endpoints.json';eventfile=parent/'batch8.json';floorfile=parent/'floors.json';bindings={str(p):sha(p) for p in (ep,eventfile,floorfile)};bindings.update({x['path']:x['sha256'] for x in json.loads(ep.read_text())['inputs'].values()});bindings.update(closure([Path(__file__)]));(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,policy='max4 failure domains, max32 swap ordinary witness checks, max4 DFS64 release sets, max4 owners, all selected queries retained, global component120s, weight0.04/FIFO256.',scope='Post-outcome component. Screen baseline failure necessary for its ordinary fixed-forbidden single-owner condition; proposals heuristic for a fresh joint root. No joint completeness or original full-cohort success claim.'))+'\n');begin=time.perf_counter();graph,digest,nodes,f,rc,queries=load_endpoints(ep);event=json.loads(eventfile.read_text());before=event['before_records'];release=set(event['released_net_ids']);selected=event['selection']['queries'];slots={e:s for s,e in enumerate(f['edge_ids'])};allowners=defaultdict(set)
for r in before:allowners[r['net_id']].add(r['source']);allowners[r['net_id']].update(f['dest_ranks'][slots[e]] for e in r['answer']['physical_edge_ids'])
keptowners={net:own for net,own in allowners.items() if net not in release};counts=Counter(r['net_id'] for r in before);cache=RemainingDelayCache(graph,digest,f,rc,out/'bounds',max_entries=256);start=time.perf_counter();deadline=start+120;f=cache.fields;rc=cache.rc;domains=[];checks=[];proposals=set();seen=set()
for branch in event['owner_repair']['attempts'][0]['branches']:
 for netstr,failure in branch['failures'].items():
  if failure is None or failure['status']!='NO_BUDGET_CAPACITY_PATH':continue
  q=failure['query'];banned=frozenset(n for net,n in branch['constraints'] if net==int(netstr));key=(q['connection_id'],banned)
  if key in seen or len(domains)>=4:continue
  seen.add(key);domain=screen(f,rc,q,banned,keptowners,failure['budget_integer'],deadline);other=Counter(n for net,own in keptowners.items() if net!=q['net_id'] for n in own);baseline=witness_in_domain(f,rc,q,domain,other,set(),failure['budget_integer'],deadline);entry=dict(query=q,budget=failure['budget_integer'],banned=sorted(banned),domain=domain,baseline=baseline);domains.append(entry)
  if baseline is not None:continue
  pairs=sorted(((old,extra) for extra in domain['candidates'] for old in release),key=lambda pair:(sum(counts[n] for n in (release-{pair[0]})|{pair[1]}),pair[1],pair[0]))
  for old,extra in pairs:
   if len(checks)>=32:break
   restored=other.copy()
   if old!=q['net_id']:restored.update(allowners[old])
   witness=witness_in_domain(f,rc,q,domain,restored,allowners[extra],failure['budget_integer'],deadline);candidate=(release-{old})|{extra};checks.append(dict(domain=len(domains)-1,old=old,extra=extra,release=sorted(candidate),witness=witness))
   if witness is not None:proposals.add(frozenset(candidate))
ordered=sorted(proposals,key=lambda owners:(sum(counts[n] for n in owners),tuple(sorted(owners))))[:4];(out/'screening.json').write_text(json.dumps(dict(domains=domains,checks=checks,proposed=[sorted(ns) for ns in ordered]))+'\n');print('screen',len(domains),len(checks),[sorted(ns) for ns in ordered],flush=True);floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(floorfile.read_text())};spans=[1+int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow'))+int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')) if n.get('type') in ('CHANX','CHANY') else 0 for n in nodes];results=[]
for i,owners in enumerate(ordered):
 kept=[r for r in before if r['net_id'] not in owners];groups=defaultdict(list)
 for q in selected:groups[q['net_id']].append(q)
 for r in before:
  if r['net_id'] in owners:groups[r['net_id']].append({k:r[k] for k in ('connection_id','net_id','source','sink')})
 def observe(branch,states,solution):
  work=out/f"attempt{i}_branch{branch['index']}";work.mkdir();(work/'branch.json').write_text(json.dumps(dict(released_net_ids=sorted(owners),branch=branch))+'\n')
  for net,state in states.items():(work/f'net{net}.json').write_text(json.dumps(state)+'\n')
  if solution is not None:(work/'joint_candidate.json').write_text(json.dumps(solution)+'\n')
 result=joint_route(f,rc,dict(groups),floors,kept,spans,4*(rc.scale//10**11),len(queries),remaining_cache=cache,max_joint_nodes=64,deadline=deadline,observer=observe,frontier='dfs',reuse_groups=True);results.append(dict(released_net_ids=sorted(owners),result=result));print(i,result['status'],flush=True)
 if result['solution'] is not None:break
cache.finalize();(out/'results.json').write_text(json.dumps(results)+'\n');(out/'cache_receipt.json').write_text(json.dumps(cache.summary())+'\n');assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,total_seconds=time.perf_counter()-begin,selected_ids=[q['connection_id'] for q in selected],global_required=len(queries),before=len(before),files={str(p):sha(p) for p in out.rglob('*') if p.is_file()}),indent=2)+'\n')
