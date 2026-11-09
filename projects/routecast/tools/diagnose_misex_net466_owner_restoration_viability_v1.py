"""All-restoration-query necessary budget gate for frozen core and unchanged kept."""
import sys,json,time,heapq,struct
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net466_owner_restoration_viability_v1_2026-10-07';out.mkdir();begin=time.perf_counter();ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';bindings={**closure([Path(__file__)]),str(ep):sha(ep),str(fp):sha(fp)};bindings.update({row['path']:row['sha256'] for row in json.loads(ep.read_text())['inputs'].values()});sources=[]
for version in [1,2]:
 parent=R/f'experiments/misex_net466_budget_path_owner_release_v{version}_2026-10-07';vp=parent/'verification.json';verified=json.loads(vp.read_text());assert verified['whole_net_owner_release_and_fixed_seed_plus_core_capacity_pass']
 for name in ['verification.json','event.json','proposals.json','core_options.json']:
  asset=parent/name;bindings[str(asset)]=sha(asset)
  if name!='verification.json':assert verified['bindings'][str(asset)]==bindings[str(asset)]
 sources.append(dict(version=version,parent=str(parent)))
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,sources=sources,policy='All four proposals in each frozen owner-release v1/v2; unchanged kept plus complete core seed. Check EVERY noncore released original connection, original budgets. Per-NET forward capped shortest distances against seed occupancy, without mutual restored-owner or parent-tree constraints. Any overbudget query rejects that fixed seed independent of restoration order. Gate-pass is necessary only, never accepted routing. No source/sink/query omissions or budget relaxation.',scope='Post-outcome diagnostic of frozen candidate seeds, not all-path core selection/native QoR or matched speed.'),indent=2)+'\n');_,_,nodes,f,rc,queries=load_endpoints(ep);qm={q['connection_id']:q for q in queries};floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};slots={e:i for i,e in enumerate(f['edge_ids'])};cases=[]
for source in sources:
 parent=Path(source['parent']);event=json.loads((parent/'event.json').read_text());options={int(n):ops for n,ops in json.loads((parent/'core_options.json').read_text()).items()};proposals=json.loads((parent/'proposals.json').read_text());core=set(options)
 for index,proposal in enumerate(proposals):
  folder=out/f"v{source['version']}_proposal{index}";folder.mkdir();kept=[x for x in event['before_records'] if x['net_id'] not in proposal['release']];core_records=[x for n,i in proposal['core_option_indices'].items() for x in options[int(n)][i]['records']];seed=kept+core_records;owners=defaultdict(set)
  for rec in seed:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
  occupancy=Counter(n for own in owners.values() for n in own);assert all(c<=f['capacities'][n] for n,c in occupancy.items());allowed=bytes(occupancy[n]<f['capacities'][n] for n in range(len(nodes)));(folder/'allowed.bin').write_bytes(allowed);groups=defaultdict(list)
  for rec in event['before_records']:
   if rec['net_id'] in proposal['release'] and rec['net_id'] not in core:groups[rec['net_id']].append(qm[rec['connection_id']])
  assert len(seed)+sum(len(g) for g in groups.values())==2172;rows=[]
  for net,qs in sorted(groups.items()):
   qs=sorted(qs,key=lambda q:q['connection_id']);assert len({q['source'] for q in qs})==1 and net not in owners;src=qs[0]['source'];budgets={q['connection_id']:max(rc.scale//10**9,(3*floors[q['source'],q['sink']]+1)//2) for q in qs};cap=max(budgets.values())+1;d=[cap]*len(nodes);d[src]=min(cap,rc.initial(src)) if allowed[src] else cap;queue=[(d[src],src)] if d[src]<cap else []
   while queue:
    delay,u=heapq.heappop(queue)
    if delay!=d[u]:continue
    for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
     v=f['dest_ranks'][edge]
     if not allowed[v]:continue
     cost=min(cap,delay+rc.increments[edge])
     if cost<d[v]:d[v]=cost;heapq.heappush(queue,(cost,v))
   file=folder/f'net{net}.bin';file.write_bytes(struct.pack('<'+str(len(nodes))+'Q',*d));failed=[q['connection_id'] for q in qs if d[q['sink']]>budgets[q['connection_id']]];rows.append(dict(net_id=net,queries=qs,budgets=budgets,cap=cap,sink_distances={q['connection_id']:d[q['sink']] for q in qs},failed_budget_connection_ids=failed,certificate_file=str(file),certificate_sha256=sha(file)))
  case=dict(version=source['version'],proposal_index=index,release=proposal['release'],allowed_file=str(folder/'allowed.bin'),seed_connections=len(seed),restoration_connections=sum(len(g) for g in groups.values()),rows=rows,necessary_gate_pass=not any(row['failed_budget_connection_ids'] for row in rows));cases.append(case);print('VIABILITY',case['version'],index,[(row['net_id'],len(row['failed_budget_connection_ids'])) for row in rows if row['failed_budget_connection_ids']],flush=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,total_paid_main_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in out.rglob('*') if p.is_file()}),indent=2)+'\n');print('GATE PASS',sum(c['necessary_gate_pass'] for c in cases),'/',len(cases),flush=True)
