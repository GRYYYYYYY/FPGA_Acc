import json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];old=root/'experiments/native_seed_timing_modes_v2_2026-10-06';new=root/'experiments/native_seed_timing_modes_v3_2026-10-06';a=json.loads((old/'receipt.json').read_text());b=json.loads((new/'receipt.json').read_text());assert len(a['results'])==len(b['results'])==4
for before,after in zip(a['results'],b['results']):
 assert before['case']==after['case'] and before['exit_code']==after['exit_code']==0
 assert before['route_sha256']==after['route_sha256'] and before['cpd_ns']==after['cpd_ns']
(new/'verification.json').write_text(json.dumps({'all_four_positive_replays_exact_route_hash_and_cpd_parity':True,'old_receipt_sha256':hashlib.sha256((old/'receipt.json').read_bytes()).hexdigest(),'new_receipt_sha256':hashlib.sha256((new/'receipt.json').read_bytes()).hexdigest(),'verifier_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n');print('All four positive replay route hashes and CPDs match')
