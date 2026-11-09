"""Replay cache keys/hits and verify all saved witnesses; certified m1 floor parity."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
ROOT=Path(__file__).resolve().parents[2];w=int(sys.argv[1]);out=ROOT/f'experiments/native_resume_reusable_rr_floors_w{w}_2026-10-07';start=time.perf_counter();r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json')
for mapping in (p['sources'],p['endpoints'],r['context_bindings']):assert all(sha(f)==h for f,h in mapping.items())
first=ROOT/f'experiments/mux_budget_move_cohort_2026-10-06/w{w}_m0/target_endpoints.json';_,digest,nodes,f,rc,queries=load_endpoints(first)
full=ROOT/f'experiments/native_resume_target_rr_floors_w{w}_m{1 if w==16 else 3}_2026-10-07';fr=json.loads((full/'receipt.json').read_text());fv=json.loads((full/'verification.json').read_text());assert fv['receipt_sha256']==sha(full/'receipt.json');known={x['query']['connection_id']:x['minimum_integer'] for x in fr['rows']};certified_index=1 if w==16 else 3
cache={};saved=None;rows=[]
for n,row in enumerate(r['rows'],1):
 rp=out/f'context/epoch_{n}/receipt.json';assert sha(rp)==row['receipt_sha256'];e=json.loads(rp.read_text());ep=ROOT/f"experiments/mux_budget_move_cohort_2026-10-06/w{w}_m{row['index']}/target_endpoints.json";meta=json.loads(ep.read_text());assert sha(ep)==e['endpoint_sha256'] and meta['graph_sha256']==e['graph_sha256']==digest and e['scale']==rc.scale
 assert e['epoch']==n and e['required_connections']==len(meta['connections']);assert len(e['answers'])==len(meta['connections']);byid={q['connection_id']:q for q in meta['connections']};assert {x['query']['connection_id'] for x in e['answers']}==set(byid)
 old=set(cache);miss=set();hits=0
 for answer in e['answers']:
  q=answer['query'];assert q==byid[q['connection_id']];key=(q['source'],q['sink']);value=(answer['minimum_integer'],answer['physical_edge_ids'])
  assert rc.path(*key,answer['physical_edge_ids'])==answer['minimum_integer']
  if key in old:assert cache[key]==value;hits+=1
  else:miss.add(key)
  if key in cache:assert cache[key]==value
  cache[key]=value
  if row['index']==certified_index:assert answer['minimum_integer']==known[q['connection_id']]
 assert len(miss)==e['miss_pairs']==row['miss_pairs'] and hits==e['hit_connections']==row['hit_connections'] and len(cache)==e['cache_entries']==row['cache_entries']
 if n==1:saved=e['answers']
 if n==5:assert e['answers']==saved and e['miss_pairs']==0
 rows.append(dict(epoch=n,index=row['index'],connections=len(e['answers']),miss_pairs=len(miss),hit_connections=hits,cache_entries=len(cache),all_witnesses_valid=True,certified_full_floor_parity=row['index']==certified_index))
assert r['invalid_inputs_rejected_without_publication'] and len(list((out/'context').glob('epoch_*')))==5
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,verification_seconds=time.perf_counter()-start,scope='Independent hit/miss and source/sink cache replay, every complete query/witness checked; full known certified floor parity at one state, exact return-state answers. Shared electrical context loader; new states witness validity alone is not independent shortest optimality proof. Invalid-input rollback assertion is producer evidence, no concurrent/durable guarantee.'),indent=2)+'\n');print(w,'verified',sum(x['connections'] for x in rows),'answers',time.perf_counter()-start,flush=True)
