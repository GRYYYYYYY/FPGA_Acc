"""All MMC primary requests at authenticated archived price epochs; diagnostic."""
import hashlib,json,sys,time
from collections import defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from class_cached_rc_endpoint_context_v1 import load_endpoints
from hybrid_bidirectional_search_v1 import Search
from ordered_owned_search_pool_v1 import SearchPool
from freeze_requested_search_result_v1 import freeze_requested
base=R/'experiments/ultraembedded_mmc_actual_old_linear_fraction_cache_workflow_v12_2026-10-10'
admission=base/'verification.json';proof=json.loads(admission.read_text());assert proof['all_cases_both_complete_arms_authenticated']
assert all(sha(p)==h for p,h in proof['bindings'].items())
model=base/'seed/model/mmc';rp=model/'receipt.json';receipt=json.loads(rp.read_text())
assert proof['bindings'][str(rp)]==sha(rp)
assert all(sha(p)==h for section in ['bindings','files'] for p,h in receipt[section].items())
endpoint=next(Path(p) for p in receipt['bindings'] if p.endswith('/endpoints.json'))
contract=R/'experiments/ordered_owned_search_pool_contract_v1_2026-10-10/verification.json';cp=json.loads(contract.read_text())
assert cp['ordered_native_parity'] and cp['requested_path_comparisons']==3600
assert all(sha(p)==h for p,h in cp['bindings'].items())
binary=R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so'
bidi=R/'experiments/bidirectional_rc_build_v2_2026-10-08/search.so'
D=R/'experiments/mmc_ordered_owned_search_pool_v1_2026-10-10';D.mkdir()
bindings=closure([Path(__file__)])
for p in [admission,rp,endpoint,contract,binary,bidi,*[model/f'round{i}.json' for i in range(2)]]:bindings[str(p)]=sha(p)
for item in json.loads(endpoint.read_text())['inputs'].values():bindings[item['path']]=item['sha256']
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,workers=2,window=4,scope='Full MMC primary requested paths at original initial and two archived round prices/affected NET lists. Archived schedule only for diagnostic parity. No fresh prospective ledger, fallback integration, independent transaction audit or fullworkflow timing gain.'),indent=2)+'\n')
begin=time.perf_counter();graph,digest,nodes,fields,rc,queries=load_endpoints(endpoint)
groups=defaultdict(list)
for q in queries:groups[q['net_id']].append(q)
assert len(queries)==115572
factory=lambda:Search(fields,rc,binary)
serial=factory();pool=SearchPool(factory,workers=2,window=4)
rows=[]
def signature(result):
 raw,parents,settled=result
 payload=[sorted(raw.items()),sorted(parents.items()),sorted(settled)]
 return hashlib.sha256(json.dumps(payload,separators=(',',':')).encode()).hexdigest()
try:
 for epoch in range(3):
  if epoch==0:prices={};weight=0;nets=sorted(groups)
  else:
   state=json.loads((model/f'round{epoch-1}.json').read_text());prices={int(k):v for k,v in state['prices'].items()};del state
   weight=rc.scale//(20*10**9);nets=receipt['rounds'][epoch-1]['affected_nets']
  requests=[]
  for net in nets:
   qs=groups[net];source=qs[0]['source'];assert all(q['source']==source for q in qs)
   requests.append((source,frozenset(q['sink'] for q in qs)))
  serial.prepare(prices,weight);pool.prepare(prices,weight)
  expected=[];tick=time.perf_counter()
  for index,(source,targets) in enumerate(requests):
   expected.append(signature(freeze_requested(source,targets,*serial.search(source,targets))))
   if (index+1)%10000==0:print('SERIAL',epoch,index+1,len(requests),flush=True)
  serial_seconds=time.perf_counter()-tick;tick=time.perf_counter();observed=hashlib.sha256()
  batch=pool.search_many(requests)
  try:
   count=0
   for index,answer in enumerate(batch):
    actual=signature(answer);assert actual==expected[index],(epoch,index,nets[index])
    observed.update(actual.encode());count+=1
    if count%10000==0:print('POOL',epoch,count,len(requests),flush=True)
   assert count==len(requests)
  finally:batch.close()
  row=dict(epoch=epoch,nets=count,connection_requests=sum(len(groups[n]) for n in nets),unique_requested_targets=sum(len(t) for _,t in requests),requested_delays_parents_settled_equal=True,comparison_digest=observed.hexdigest(),serial_search_snapshot_hash_seconds=serial_seconds,pool_search_snapshot_hash_seconds=time.perf_counter()-tick)
  rows.append(row);(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print('EPOCH DONE',json.dumps(row),flush=True)
finally:pool.close();serial.close()
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,files={str(D/'protocol.json'):sha(D/'protocol.json'),str(D/'progress.json'):sha(D/'progress.json')},epochs=rows,complete_all_initial_and_two_feedback_primary_requests_equal=True,required_connections=len(queries),local_diagnostic_seconds=time.perf_counter()-begin,scope='All requested delay/parent/settled signatures match serial hybrid at authenticated original MMC archived prices/schedules. SHA256 comparison, all requests without sampling. Timing includes Python snapshots/hash; fixed serial-first order, no stable causal speedup. Not a fresh prospective transaction model, full independent XML/Fraction audit, native routing or fullworkflow gain.'),indent=2)+'\n')
print('PASS full MMC ordered pool requested-path parity',flush=True)
