"""Independent fixed-order capacity-subtraction proof over the broad tree pool."""
import sys,json,time
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from unique_source_hash_validation_v1 import merge_expected,validate_expected
out=R/'experiments/misex_net466_tree_pool_v2_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());bindings={};merge_expected(bindings,r['bindings']);merge_expected(bindings,r['files']);merge_expected(bindings,closure([Path(__file__)]));bindings[str(rp)]=sha(rp);validate_expected(bindings);assert json.loads((out/'candidate.json').read_text()) is None;e=json.loads((out/'event.json').read_text());_,_,_,f,_,_=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');slots={edge:i for i,edge in enumerate(f['edge_ids'])};sources=[]
for v in range(5,18):
 p=R/f'experiments/misex_net466_extra_owner_joint_v{v}_2026-10-07';sources.append((p,json.loads((p/'receipt.json').read_text())))
def occupied(records):return {rec['source'] for rec in records}|{f['dest_ranks'][slots[edge]] for rec in records for edge in rec['answer']['physical_edge_ids']}
rows=[];deadline=time.perf_counter()+120
for attempt in r['attempts']:
 if attempt['status']!='POOL_EXHAUSTED':rows.append(dict(attempt=attempt['index'],status='PRODUCER_INCOMPLETE_NO_EXHAUSTION_CLAIM'));continue
 release=set(attempt['release']);required=defaultdict(set);kept=defaultdict(list)
 for rec in e['before_records']:
  if rec['net_id'] in release:required[rec['net_id']].add(rec['connection_id'])
  else:kept[rec['net_id']].append(rec)
 for q in e['selection']['queries']:required[q['net_id']].add(q['connection_id'])
 variants={net:{} for net in required}
 def add(net,records):
  if {rec['connection_id'] for rec in records}!=required[net]:return
  key=tuple(sorted((rec['connection_id'],tuple(rec['answer']['physical_edge_ids'])) for rec in records));variants[net][key]=occupied(records)
 for net in required:add(net,[rec for rec in e['before_records'] if rec['net_id']==net])
 for source,sr in sources:
  for a in sr['attempts']:
   if set(a['release'])!=release:continue
   for branch in a['branches']:
    for net in required:
     p=source/f"attempt{a['index']}_branch{branch['index']}"/f'net{net}.json'
     if p.exists():
      s=json.loads(p.read_text())
      if s['failure'] is None:add(net,[rec for rec in s['records'] if rec['net_id']==net])
 assert {str(net):len(variants[net]) for net in required}==attempt['variant_counts'];nets=sorted(required);base=Counter(node for records in kept.values() for node in occupied(records));remaining={n:f['capacities'][n]-base[n] for choices in variants.values() for nodes in choices.values() for n in nodes};assert all(c>=0 for c in remaining.values());visits=0;limited=False
 def possible(index):
  global visits,limited
  if time.perf_counter()>=deadline or visits>=1000000:limited=True;return None
  visits+=1
  if index==len(nets):return True
  for nodes in variants[nets[index]].values():
   if any(remaining[n]<=0 for n in nodes):continue
   for n in nodes:remaining[n]-=1
   result=possible(index+1)
   for n in nodes:remaining[n]+=1
   if result is not False:return result
  return False
 result=possible(0);assert result is not True,'Independent solver found a capacity-feasible tree combination';rows.append(dict(attempt=attempt['index'],status='VERIFIED_FINITE_POOL_EXHAUSTED' if result is False else 'VERIFIER_LIMIT_NO_PROOF',nodes=visits));print(rows[-1],flush=True)
validate_expected(bindings);(out/'pool_exhaustion_verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Independent ascending NET order, capacity subtraction over every available frozen variant; bounded results explicitly labeled. No global-path/native infeasibility or workflow gain.'),indent=2)+'\n')
