"""Recombine complete expanded NET trees across audited rounds, charge protected seed once."""
import sys,json,time
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from tree_variant_capacity_packing_v1 import pack_variants
out=R/'experiments/misex_net466_expanded_tree_pool_v1_2026-10-07';out.mkdir();begin=time.perf_counter();parent=R/'experiments/misex_net466_expanded_negotiation_v1_2026-10-07';vp=parent/'branch_verification_dedup.json';v=json.loads(vp.read_text());assert v['all_xml_rc_tree_local_capacity_complete_scope_and_history_checks_pass'];rp=parent/'receipt.json';assert sha(rp)==v['bindings'][str(rp)];pr=json.loads(rp.read_text());ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';bindings={**closure([Path(__file__)]),str(vp):sha(vp),str(rp):sha(rp),str(ep):sha(ep)};bindings.update({x['path']:x['sha256'] for x in json.loads(ep.read_text())['inputs'].values()})
for name in ['seed.json','event.json','protocol.json']:bindings[str(parent/name)]=sha(parent/name);assert bindings[str(parent/name)]==v['bindings'][str(parent/name)]
p=json.loads((parent/'protocol.json').read_text());seed=json.loads((parent/'seed.json').read_text());groups={int(n):qs for n,qs in p['groups'].items()};_,_,nodes,f,rc,queries=load_endpoints(ep);slots={e:i for i,e in enumerate(f['edge_ids'])};seedowners=defaultdict(set)
def own(records):return {x['source'] for x in records}|{f['dest_ranks'][slots[e]] for x in records for e in x['answer']['physical_edge_ids']}
for rec in seed:seedowners[rec['net_id']].update(own([rec]))
base=Counter(n for s in seedowners.values() for n in s);pools={n:[] for n in groups};signatures=defaultdict(set)
for branch in pr['branches']:
 for n in sorted(groups):
  file=parent/f"round{branch['index']}"/f'net{n}.json'
  if not file.exists():continue
  assert sha(file)==v['bindings'][str(file)];bindings[str(file)]=sha(file);state=json.loads(file.read_text())
  if state['failure'] is not None:continue
  records=state['records'];assert len(records)==len(groups[n]) and {x['connection_id'] for x in records}=={q['connection_id'] for q in groups[n]};sig=tuple((x['connection_id'],tuple(x['answer']['physical_edge_ids'])) for x in records)
  if sig not in signatures[n]:pools[n].append(dict(records=records,nodes=sorted(own(records)-seedowners[n]),origin=str(file)));signatures[n].add(sig)
(out/'seed.json').write_text(json.dumps(seed)+'\n');(out/'event.json').write_text((parent/'event.json').read_text());(out/'pool.json').write_text(json.dumps(pools)+'\n');(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,groups=groups,search_seconds=120,max_nodes=100000,policy='All complete variants from all12 audited rounds; node choices subtract only same NET seed-owned nodes so protected trunk charged once, other NET seed occupancy remains. All27groups/full2172CID required, compact paths with immutable seed. Finite pooling only, no all-path/native proof.'),indent=2)+'\n');assert all(sha(k)==h for k,h in bindings.items());start=time.perf_counter();result=pack_variants(f['capacities'],base,{n:[op['nodes'] for op in ops] for n,ops in pools.items()},max_nodes=100000,deadline=start+120);solution=None
if result['status']=='FOUND_POOL_BATCH':
 records=seed+[rec for n,i in result['chosen_option_indices'].items() for rec in pools[n][i]['records']];assert len({x['connection_id'] for x in records})==len(records)==2172;owners=defaultdict(set)
 for rec in records:owners[rec['net_id']].update(own([rec]))
 ledger=Counter(n for s in owners.values() for n in s);assert all(c<=f['capacities'][n] for n,c in ledger.items());solution=dict(records=sorted(records,key=lambda x:x['connection_id']),ledger=dict(ledger),failure=None,completed_connections=len(records),required_connections=len(queries),pending_connection_ids=sorted({q['connection_id'] for q in queries}-{x['connection_id'] for x in records}),selected_origins={str(n):pools[n][i]['origin'] for n,i in result['chosen_option_indices'].items()})
checks=[];core=sorted(pools)
if result['status']=='POOL_EXHAUSTED':
 for n in sorted(pools):
  remaining=[x for x in core if x!=n];probe=pack_variants(f['capacities'],base,{x:[op['nodes'] for op in pools[x]] for x in remaining},max_nodes=100000,deadline=start+120);checks.append(dict(removed_net=n,nets=remaining,result=probe))
  if probe['status']=='POOL_EXHAUSTED':core=remaining
(out/'candidate.json').write_text(json.dumps(solution)+'\n');assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,result=result,variant_counts={n:len(ops) for n,ops in pools.items()},core_nets=core,diagnostic_deletion_checks=checks,completed=None if solution is None else len(solution['records']),required=len(queries),total_paid_main_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in out.iterdir() if p.is_file()}),indent=2)+'\n');print('POOL',result, 'CORE',core, 'COUNTS', {n:len(ops) for n,ops in pools.items()},flush=True)
