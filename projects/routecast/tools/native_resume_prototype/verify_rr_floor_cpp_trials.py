"""Independent decode, endpoint/units binding, exact path sums and certified-floor parity."""
import json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];build=ROOT/'build/native_resume_rr_floor_cpp_2026-10-07/receipt.json';b=json.loads(build.read_text());assert sha(b['binary'])==b['binary_sha256'] and sha(b['source'])==b['source_sha256'];rows=[];bindings={str(build):sha(build)}
for w,i in ((16,1),(32,3)):
 out=ROOT/f'experiments/native_resume_rr_floor_cpp_w{w}_m{i}_2026-10-07';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json') and p['build_receipt_sha256']==sha(build)
 assert all(sha(f)==h for f,h in p['inputs'].items()) and all(sha(f)==h for f,h in p['sources'].items())
 payload=out/'graph_queries.bin';assert sha(payload)==p['payload_sha256'];data=payload.read_bytes();assert len(data)%8==0;words=[v[0] for v in struct.iter_unpack('<Q',data)];magic,n,m,q=words[:4];assert magic==0x5243464c4f4f5231;cursor=4
 def take(count):
  global cursor
  values=words[cursor:cursor+count];cursor+=count;assert len(values)==count;return values
 offsets=take(n+1);dest=take(m);weight=take(m);cap=take(n);initial=take(n);flat=take(q*3);assert cursor==len(words) and offsets[0]==0 and offsets[-1]==m and offsets==sorted(offsets)
 queries={flat[j]:(flat[j+1],flat[j+2]) for j in range(0,len(flat),3)};assert len(queries)==q==r['connections'];assert set(queries)==set(p['selected_connection_ids'])
 ep=ROOT/f'experiments/mux_budget_move_cohort_2026-10-06/w{w}_m{i}/target_endpoints.json';meta=json.loads(ep.read_text());assert p['graph_sha256']==meta['graph_sha256'];byid={x['connection_id']:x for x in meta['connections']}
 for cid,pair in queries.items():assert pair==(byid[cid]['source'],byid[cid]['sink'])
 prior=ROOT/f'experiments/native_resume_critical_rr_floors_w{w}_m{i}_2026-10-07';pr=json.loads((prior/'receipt.json').read_text());pv=json.loads((prior/'verification.json').read_text());assert pv['receipt_sha256']==sha(prior/'receipt.json')==p['prior_receipt_sha256'] and pr['scale']==p['scale'];floors={x['query']['connection_id']:x['minimum_integer'] for x in pr['rows']}
 previous=None
 for run in r['runs']:
  f=out/f"output_{run['repeat']}.jsonl";assert sha(f)==run['output_sha256'];actual=[json.loads(s) for s in f.read_text().splitlines()];assert len(actual)==q and {x['connection_id'] for x in actual}==set(queries)
  for x in actual:
   u,target=queries[x['connection_id']];value=initial[u];assert cap[u]>0
   for slot in x['slots']:
    assert offsets[u]<=slot<offsets[u+1];u=dest[slot];assert cap[u]>0;value+=weight[slot]
   assert u==target and value==x['minimum_integer']==floors[x['connection_id']]
  if previous is not None:assert actual==previous
  previous=actual
 for f in (out/'protocol.json',out/'receipt.json',payload,prior/'receipt.json',prior/'verification.json'):bindings[str(f)]=sha(f)
 rows.append(dict(width=w,connections=q,repeats=len(r['runs']),all_exact_sums_and_certified_floors_equal=True,preparation_seconds=r['preparation_seconds'],export_seconds=r['payload_export_seconds'],query_process_seconds=[x['query_process_seconds'] for x in r['runs']],trial_total_seconds=r['trial_total_seconds']))
out=ROOT/'experiments/native_resume_rr_floor_cpp_comparison_2026-10-07';out.mkdir(exist_ok=False);(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,verifier_sha256=sha(Path(__file__)),scope='Independent binary decoding, endpoint and scale binding, CSR continuity and exact path sums; floor optimality reused from earlier subset certificates. Electrical graph export shares original loader; no independent native shared-tree model validation, persistent cache or end-to-end route-gain claim.'),indent=2)+'\n');print(rows)
