"""Verify all completed native receipts and immutable model payloads once at stage close."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prince_input_mean_trial_v1_2026-10-20'
def main():
 p=D/'verification.json';v=json.loads(p.read_text());pp=D/'protocol.json';jobs=json.loads(pp.read_text())['jobs'];checked={}
 for row in v['rows']:
  for path,h in row['files'].items():
   if path not in checked:assert sha(path)==h;checked[path]=h
 for job in jobs:
  model=job['input_model'];path=model['payload'];assert sha(path)==model['sha256'];checked[path]=model['sha256']
 out=D/'receipt_integrity_verification_v1.json';assert not out.exists();out.write_text(json.dumps(dict(status='ALL36_NATIVE_CASE_RECEIPTS_AND_MODELS_INTEGRITY_PASS',cases=len(v['rows']),verified_files=len(checked),bindings={str(p):sha(p),str(pp):sha(pp),str(Path(__file__)):sha(__file__)}),indent=2)+'\n');print('NATIVE_RECEIPT_INTEGRITY_PASS',len(v['rows']),len(checked))
if __name__=='__main__':main()
