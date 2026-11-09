"""Verify all seven paired component SAT receipts and exact frozen inputs."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/actual_source_bank_cones_sat_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for p,h in json.loads((D/'protocol.json').read_text())['bindings'].items():assert sha(Path(p))==h,p
 rows=json.loads((D/'results.json').read_text())['rows'];assert len(rows)==14;groups={r['source_instance'] for r in rows};assert len(groups)==7
 for n in groups:
  pair=[r for r in rows if r['source_instance']==n];assert {r['mode'] for r in pair}=={'repair','unrepaired_negative'};assert pair[0]['compared_bits']==pair[1]['compared_bits']
 for r in rows:
  for p,h in r['bindings'].items():assert sha(R/p)==h,p
  logpath=next(R/p for p in r['bindings'] if p.endswith('/yosys.log'));log=logpath.read_text();assert 'Found and reported 0 problems.' in log
  if r['mode']=='repair':assert r['exit_code']==0 and r['proof_passed'] and 'no model found: SUCCESS' in log
  else:assert r['exit_code']==1 and r['negative_failed'] and 'proof did fail' in log
 out={'status':'ALL_7_ACTUAL_SOURCE_READ_CONES_SAT_VERIFIED_WITH_NEGATIVE_CONTROLS','groups':sorted(groups),'unique_compared_read_AND_output_bits':sum(r['compared_bits'] for r in rows if r['mode']=='repair'),'bindings':{str(p.relative_to(R)):sha(p) for p in [D/'protocol.json',D/'results.json']},'scope':'Actual repaired read cones match original cones with bank selector inputs replaced by sampled-Q symbolic inputs for arbitrary binary RAM output bits and sampled bank values. All original live-selector negative controls fail. RAM state and bank FF Q are abstract inputs; sequential/source/unknown-state/collision/native equivalence remains unproven.'};(D/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
if __name__=='__main__':main()
