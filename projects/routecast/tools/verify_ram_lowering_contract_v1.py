"""Verify paired collision SAT hypotheses and independent noncollision HDL witness."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'standard_ram_collision_sat_v2_2026-10-21';D=E/'ram_ownport_lowering_xsim_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for d in [S,D]:
  for p,h in json.loads((d/'protocol.json').read_text())['bindings'].items():assert sha(Path(p))==h,p
 rows=json.loads((S/'results.json').read_text())['rows'];assert len(rows)==4
 for row in rows:
  log=(S/row['hypothesis']/'yosys.log').read_text()
  if row['hypothesis']=='old_old':assert row['exit_code']==0 and row['sat_proof_success'] and 'no model found: SUCCESS' in log
  else:assert row['exit_code']==1 and row['proof_failed'] and 'proof did fail' in log
 stages=json.loads((D/'results.json').read_text())['rows'];assert len(stages)==3 and all(r['exit_code']==0 for r in stages);log=(D/'xsim.log').read_text();assert 'OWNPORT_LOWERING_MISMATCH_CONFIRMED original=2 lowered=1 crossport_collision=0' in log
 tb=(D/'tb.v').read_text();assert tb.count(".addr1(1'b0),.addr2(1'b1)")==2 and tb.count(".we2(1'b0)")==2;assert 'initial begin' in tb and 'data1=2' in tb
 assert 'Found and reported 0 problems.' in (D/'export.log').read_text()
 out={'status':'RAW_NOMEM2REG_RAM_IR_NOT_QUALIFIED_AS_FUNCTIONAL_REFERENCE','sat_hypotheses':rows,'independent_hdl_witness':'Same A1/W2 source and its pinned raw proc IR, second public write data2 yields original own-port2 versus lowered1. Address1=0/address2=1 throughout, writer2=0, no initialization assumptions.','bindings':{str(p.relative_to(R)):sha(p) for p in [D/'tb.v',D/'lowered.v',D/'export.ys',D/'export.log',D/'xsim.log']},'scope':'Raw primitive expansion/lowering configuration only, not complete standard Parmys hard-block synthesis. Prior read-after-write noncollision trace remains true but insufficient for functional equivalence.'};(D/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
if __name__=='__main__':main()
