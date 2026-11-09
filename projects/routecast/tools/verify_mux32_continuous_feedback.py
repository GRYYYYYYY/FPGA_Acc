"""Bind continuous stage clocks, fresh dependencies and final state evidence."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux32_continuous_feedback_2026-10-07';rp=out/'receipt.json';pp=out/'protocol.json';r=json.loads(rp.read_text());p=json.loads(pp.read_text());assert r['protocol_sha256']==sha(pp);assert r['status']=='COMPLETE_STATIC_CANONICAL_CANDIDATE' and r['error'] is None;assert all(sha(f)==h for f,h in p['sources'].items());assert len(r['rows'])==len(p['sequence'])==19
for row,job in zip(r['rows'],p['sequence']):
 assert (row['stage'],row['kind'])==(job['stage'],job['kind']) and row['exit_code']==0
 assert sha(out/f"{row['stage']}_{row['kind']}.log")==row['log_sha256']
assert sum(row['external_seconds'] for row in r['rows'])<=r['external_wall_seconds']
keys=['critical','ascending','reverse','longest','shortest','revisit','retry'];previous=None;bindings={str(rp):sha(rp),str(pp):sha(pp)};wire=[]
for key in keys:
 base=ROOT/f'experiments/mux32_continuous_{key}_2026-10-07';cp=base/'candidate.json';s=json.loads((base/'receipt.json').read_text());v=json.loads((base/'verification.json').read_text());protocol=json.loads((base/'protocol.json').read_text())
 assert s['candidate_sha256']==sha(cp) and v['receipt_sha256']==sha(base/'receipt.json')
 if previous is not None:assert protocol['inputs'][str(previous)]==sha(previous)
 assert all(sha(f)==h for f,h in protocol['inputs'].items())
 previous=cp;wire.append(v['channel_union_wirelength']);bindings.update({str(f):sha(f) for f in (cp,base/'receipt.json',base/'verification.json')})
base=ROOT/'experiments/mux32_continuous_canonical_2026-10-07';v=json.loads((base/'verification.json').read_text());join=json.loads((base/'state_join_verification.json').read_text());assert v['joint_nonregression'] and v['zero_fixups'] and v['physical_paths_preserved'];assert join['stable_connection_endpoints_joined']==1929 and join['canonical_ledger_matches_candidate'];assert all(sha(f)==h for f,h in join['bindings'].items())
bindings.update({str(f):sha(f) for f in (base/'verification.json',base/'state_join_verification.json')})
reference=ROOT/'experiments/mux32_limit_retry_tree_2026-10-07/candidate.json';identical=sha(previous)==sha(reference)
result=dict(source_sha256=sha(Path(__file__)),bindings=bindings,continuous_external_seconds=r['external_wall_seconds'],all_stage_exits_zero=True,all_proofs_inside_external_clock=True,wire_sequence=wire,final_candidate_byte_identical_development_reference=identical,canonical_cpd_ns=v['canonical_cpd_ns'],canonical_wirelength=v['canonical_wirelength'],scope=p['scope'])
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result['continuous_external_seconds'],wire,identical)
