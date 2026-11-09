"""Certified full-output parity and independently counted in-call memo keys."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
old=R/'experiments/dsip_pending_prefix_cache256_dfs64_v4_2026-10-07';out=R/'experiments/dsip_prefix_edge_context_v7_2026-10-07';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());reference=json.loads((old/'verification.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');bindings={**p['inputs'],**p['sources'],**r['files'],**reference['bindings'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json'),str(old/'verification.json'):sha(old/'verification.json')};assert all(sha(k)==v for k,v in bindings.items());(out/'parity_verification_protocol.json').write_text(json.dumps(dict(bindings=bindings))+'\n');files=[];keys={};requests=0;memo_records=0
for file in sorted(old.glob('branch*/*.json')):
 other=out/file.relative_to(old);assert json.loads(file.read_text())==json.loads(other.read_text());bindings[str(file)]=sha(file);bindings[str(other)]=sha(other);files.append(str(file.relative_to(old)))
result=json.loads((out/'joint_result.json').read_text());original=json.loads((old/'joint_result.json').read_text());assert result['solution']==original['solution'] and result['branches']==original['branches'] and result['status']==original['status']
for branch in result['branches']:
 directory=out/f"branch{branch['index']}"
 for file in directory.glob('net*.json'):
  net=int(file.stem[3:]);key=(net,tuple(sorted(n for owner,n in branch['constraints'] if owner==net)));state=json.loads(file.read_text());requests+=1
  if key in keys:assert state==keys[key]
  else:keys[key]=state;memo_records+=len(state['records'])
assert result['low_level_requests']==requests and result['low_level_computations']==len(keys) and result['low_level_reuses']==requests-len(keys) and result['memo_entries']==len(keys) and result['memo_record_count']==memo_records;assert all(sha(k)==v for k,v in bindings.items());(out/'parity_verification.json').write_text(json.dumps(dict(bindings=bindings,all_branch_and_candidate_files_json_equal=len(files),low_level_requests=requests,unique_constraint_keys=len(keys),reuses=requests-len(keys),memo_record_count=memo_records,scope='All actual paths/states identical to independently audited reference, including forbidden/RC/XML/parents/capacity/unaffected identity; no new native/global quality or timing control.'),indent=2)+'\n');print('PASS certified memo parity',len(files),requests,len(keys))
