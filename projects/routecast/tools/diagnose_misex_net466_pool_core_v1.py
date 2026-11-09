"""Finite whole-tree pool unsatisfied NET subset; dropped groups are diagnostic only."""
import sys,json,time
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from tree_variant_capacity_packing_v1 import pack_variants
parent=R/'experiments/misex_net466_tree_pool_v4_2026-10-07';poolfile=parent/'pool_attempt0.json';eventfile=parent/'event.json';ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';out=R/'experiments/misex_net466_pool_core_v1_2026-10-07';out.mkdir();bindings={**closure([Path(__file__)]),str(poolfile):sha(poolfile),str(eventfile):sha(eventfile),str(ep):sha(ep)};bindings.update({row['path']:row['sha256'] for row in json.loads(ep.read_text())['inputs'].values()});release=[24,113,157,165,180,258,331,334,384];(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,release=release,scope='Finite frozen complete-tree variant conflict core. Dropping NET constraints is diagnostic relaxation only, never a route candidate, scope reduction or commit.',nodes=100000,deadline_seconds=120,policy='Ascending NET greedy deletions only on certified finite packing exhaustion, then witness each final-core deletion.'),indent=2)+'\n');_,_,_,f,rc,queries=load_endpoints(ep);slots={edge:i for i,edge in enumerate(f['edge_ids'])};e=json.loads(eventfile.read_text());pool={int(net):options for net,options in json.loads(poolfile.read_text()).items()};groups=defaultdict(set);owners=defaultdict(set)
def own(records):return {r['source'] for r in records}|{f['dest_ranks'][slots[edge]] for r in records for edge in r['answer']['physical_edge_ids']}
for rec in e['before_records']:
 if rec['net_id'] in release:groups[rec['net_id']].add(rec['connection_id'])
 else:owners[rec['net_id']].update(own([rec]))
for q in e['selection']['queries']:groups[q['net_id']].add(q['connection_id'])
assert set(pool)==set(groups);querymap={q['connection_id']:q for q in queries}
for net,options in pool.items():
 for option in options:
  assert {r['connection_id'] for r in option['records']}==groups[net];assert sorted(own(option['records']))==option['nodes'];parents={}
  for rec in option['records']:
   assert all(rec[k]==querymap[rec['connection_id']][k] for k in ['net_id','source','sink']);assert rc.path(rec['source'],rec['sink'],rec['answer']['physical_edge_ids'])==rec['answer']['delay']<=rec['budget_integer'];u=rec['source']
   for edge in rec['answer']['physical_edge_ids']:
    s=slots[edge];assert f['row_offsets'][u]<=s<f['row_offsets'][u+1];v=f['dest_ranks'][s];parent=(u,edge);assert v not in parents or parents[v]==parent;parents[v]=parent;u=v
base=Counter(n for ownnodes in owners.values() for n in ownnodes);deadline=time.perf_counter()+120;checks=[]
def solve(nets):return pack_variants(f['capacities'],base,{net:[option['nodes'] for option in pool[net]] for net in nets},max_nodes=100000,deadline=deadline)
core=sorted(pool);initial=solve(core);assert initial['status']=='POOL_EXHAUSTED';print('Full pool exhausted',initial['search_nodes'],flush=True)
for net in sorted(pool):
 candidate=[n for n in core if n!=net];result=solve(candidate);checks.append(dict(removed_net=net,nets=candidate,result=result));print('Drop',net,result['status'],result['search_nodes'],flush=True)
 if result['status']=='POOL_EXHAUSTED':core=candidate
witnesses=[]
for net in core:
 candidate=[n for n in core if n!=net];result=solve(candidate);witnesses.append(dict(removed_net=net,nets=candidate,result=result))
assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,release=release,initial=initial,deletion_checks=checks,core_nets=core,core_deletion_witnesses=witnesses,irreducible_in_pool=all(w['result']['status']=='FOUND_POOL_BATCH' for w in witnesses),scope='Unsatisfied finite tree-variant subset under fixed kept; no omitted NET is accepted in routing and no global/native infeasibility or workflow gain.'),indent=2)+'\n');print('Pool core',core,flush=True)
