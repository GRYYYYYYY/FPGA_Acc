"""Frozen complete-NET tree pool packing from archived negotiated proposals."""
import sys,json,time,copy
run_begin=time.perf_counter()
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from unique_source_hash_validation_v1 import merge_expected,validate_expected
from tree_variant_capacity_packing_v1 import pack_variants
from nonzero_rc_endpoint_context import load_endpoints
parent=R/'experiments/misex_net466_extra_owner_joint_v17_2026-10-07';out=R/'experiments/misex_net466_tree_pool_v3_2026-10-07';out.mkdir();rp=parent/'receipt.json';receipt=json.loads(rp.read_text());bindings={**receipt['bindings'],**receipt['files'],**closure([Path(__file__)]),str(rp):sha(rp)};sources=[]
for version in range(5,18):
 source=R/f'experiments/misex_net466_extra_owner_joint_v{version}_2026-10-07';source_receipt=json.loads((source/'receipt.json').read_text());proof=source/'branch_verification_dedup.json';verified=json.loads(proof.read_text());merge_expected(bindings,verified['bindings']);bindings[str(proof)]=sha(proof);bindings[str(source/'receipt.json')]=sha(source/'receipt.json');merge_expected(bindings,source_receipt['files']);sources.append((source,source_receipt))
print('INITIAL_UNIQUE_CONTENT_CHECK',len(bindings),flush=True);preflight_begin=time.perf_counter();initial_validation=validate_expected(bindings);preflight_seconds=time.perf_counter()-preflight_begin;print('INITIAL_CONTENT_CHECK_PASSED',initial_validation,flush=True);(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,max_candidates=8,max_search_nodes=100000,deadline_seconds=120,pool='For each same release scope, complete original trees plus all successful complete whole-NET proposals from 13 independently physically-audited trials v5..v17 with same release scope; deduplicate by complete physical paths. Preserve fixed kept and every selected/released CID.',order='Dynamic fewest currently capacity-compatible options then NET ID; original option first then numeric round order; exact node-union capacity pruning.',scope='Finite frozen candidate tree combinations, not new path generation/global solver/native or workflow gain.'),indent=2)+'\n');begin=time.perf_counter();event=json.loads((parent/'event.json').read_text());(out/'event.json').write_text(json.dumps(event)+'\n');_,_,nodes,f,rc,queries=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');slots={e:i for i,e in enumerate(f['edge_ids'])}
def occupied(records):
 own=set()
 for rec in records:own.add(rec['source']);own.update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
 return own
attempts=[];solution=None;deadline=time.perf_counter()+120
for a in receipt['attempts']:
 release=set(a['release']);kept=[r for r in event['before_records'] if r['net_id'] not in release];groups=defaultdict(set)
 for rec in event['before_records']:
  if rec['net_id'] in release:groups[rec['net_id']].add(rec['connection_id'])
 for q in event['selection']['queries']:groups[q['net_id']].add(q['connection_id'])
 pool={n:[] for n in groups};seen={n:set() for n in groups}
 def add(net,records,origin):
  records=sorted(records,key=lambda r:r['connection_id'])
  if {r['connection_id'] for r in records}!=groups[net]:return
  key=tuple((r['connection_id'],tuple(r['answer']['physical_edge_ids'])) for r in records)
  if key not in seen[net]:seen[net].add(key);pool[net].append(dict(records=records,origin=origin,nodes=occupied(records)))
 for net in groups:add(net,[r for r in event['before_records'] if r['net_id']==net],'original')
 for source,source_receipt in sources:
  for source_attempt in source_receipt['attempts']:
   if set(source_attempt['release'])!=release:continue
   for branch in source_attempt['branches']:
    d=source/f"attempt{source_attempt['index']}_branch{branch['index']}"
    for net in groups:
     p=d/f'net{net}.json'
     if p.exists():
      state=json.loads(p.read_text())
      if state['failure'] is None:add(net,[r for r in state['records'] if r['net_id']==net],str(p))
 nets=sorted(groups,key=lambda net:(len(pool[net]),net));owners=defaultdict(set)
 for rec in kept:owners[rec['net_id']].update(occupied([rec]))
 ledger=Counter(n for own in owners.values() for n in own);assert all(v<=f['capacities'][n] for n,v in ledger.items());chosen={};visits=0;limited=False
 result=pack_variants(f['capacities'],ledger,{net:[option['nodes'] for option in pool[net]] for net in nets},max_nodes=100000,deadline=deadline);found=result['status']=='FOUND_POOL_BATCH';visits=result['search_nodes'];status=result['status']
 if found:
  chosen={net:pool[net][index] for net,index in result['chosen_option_indices'].items()}
  for option in chosen.values():ledger.update(option['nodes'])
 attempts.append(dict(index=a['index'],release=a['release'],variant_counts={str(n):len(pool[n]) for n in nets},net_order=nets,search_nodes=visits,status=status));print(attempts[-1],flush=True)
 if found:
  records=kept+[r for n in nets for r in chosen[n]['records']];expected={r['connection_id'] for r in event['before_records']}|set(event['selection']['requested_connection_ids']);assert {r['connection_id'] for r in records}==expected
  solution=dict(records=sorted(records,key=lambda r:r['connection_id']),ledger={n:c for n,c in ledger.items() if c},completed_connections=len(records),required_connections=len(queries),failure=None,pending_connection_ids=sorted({q['connection_id'] for q in queries}-expected),selected_origins={str(n):chosen[n]['origin'] for n in nets},released_net_ids=a['release']);break
 if time.perf_counter()>=deadline:break
(out/'candidate.json').write_text(json.dumps(solution)+'\n');print('FINAL_UNIQUE_CONTENT_CHECK',len(bindings),flush=True);final_validation=validate_expected(bindings);(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,attempts=attempts,completed=None if solution is None else len(solution['records']),required=len(queries),total_component_seconds=time.perf_counter()-begin,total_paid_main_seconds=time.perf_counter()-run_begin,source_hash_preflight_seconds=preflight_seconds,initial_validation=initial_validation,final_validation=final_validation,files={str(p):sha(p) for p in out.rglob('*') if p.is_file()}),indent=2)+'\n')
