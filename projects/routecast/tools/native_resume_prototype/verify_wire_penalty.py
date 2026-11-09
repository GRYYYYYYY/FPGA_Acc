"""Independent integer Dijkstra replay of fixed weighted query payloads."""
import json,struct,heapq,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2]
out=ROOT/'experiments/native_resume_wire_penalty_comparison_2026-10-07';out.mkdir(exist_ok=False);start=time.perf_counter();rows=[];bindings={str(Path(__file__)):sha(Path(__file__))}
for w,i in ((16,1),(32,3)):
 for penalty in ('0.001','0.01','0.1'):
  d=ROOT/f'experiments/native_resume_wire_penalty_{penalty}_w{w}_m{i}_2026-10-07';r=json.loads((d/'receipt.json').read_text());p=json.loads((d/'protocol.json').read_text());assert sha(d/'protocol.json')==r['protocol_sha256'];assert all(sha(f)==h for f,h in p['inputs'].items());bindings.update(p['inputs']);bindings[str(d/'receipt.json')]=sha(d/'receipt.json');nets=[]
  for idx,row in enumerate(r['rows']):
   payload=d/f'net_{idx}.bin';result=d/f'net_{idx}.jsonl';assert sha(payload)==row['payload_sha256'] and sha(result)==row['output_sha256'];bindings.update({str(payload):sha(payload),str(result):sha(result)})
   raw=payload.read_bytes();a=struct.unpack('<'+'Q'*(len(raw)//8),raw);magic,n,m,q=a[:4];assert magic==0x5243464c4f4f5231;pos=4
   def take(count):
    global pos
    v=a[pos:pos+count];pos+=count;return v
   offsets=take(n+1);dest=take(m);weight=take(m);capacity=take(n);initial=take(n);triples=take(q*3);assert pos==len(a)
   answers={x['connection_id']:x for x in map(json.loads,result.read_text().splitlines())};groups={}
   for cid,src,sink in zip(triples[::3],triples[1::3],triples[2::3]):groups.setdefault(src,[]).append((cid,sink))
   for src,queries in groups.items():
    distances={src:initial[src]};heap=[(initial[src],src)];targets={sink for _,sink in queries}
    while heap and targets:
     cost,node=heapq.heappop(heap)
     if distances[node]!=cost:continue
     targets.discard(node)
     for slot in range(offsets[node],offsets[node+1]):
      v=dest[slot];next_cost=cost+weight[slot]
      if capacity[v] and next_cost<distances.get(v,2**64):distances[v]=next_cost;heapq.heappush(heap,(next_cost,v))
    assert not targets
    for cid,sink in queries:assert answers[cid]['minimum_integer']==distances[sink]
   assert row['wire_budget_pass']==(row['new_wire']<=row['old_wire']);assert row['all_path_delays_no_worse']==all(x['conditional_integer']<=x['current_path_additive_integer'] for x in row['records'])
   nets.append({k:row[k] for k in ('net','old_wire','new_wire','wire_budget_pass','all_path_delays_no_worse')})
  rows.append(dict(width=w,penalty_ns=penalty,nets=nets,all_net_budgets_pass=all(x['wire_budget_pass'] for x in nets),diagnostic_seconds=r['total_seconds']));print(w,penalty,rows[-1]['all_net_budgets_pass'],flush=True)
assert all(sha(f)==h for f,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,verification_seconds=time.perf_counter()-start,scope='Independent shortest weighted distance replay. WholeNET union counts from producer; prior native accounting definition. No native materialization, heldout inference or end-to-end speed claim.'),indent=2)+'\n')
