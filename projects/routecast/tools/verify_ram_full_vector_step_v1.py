"""Verify completed full2048-row encoded-state crosscheck, not whole source equivalence."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/ram_ownport_fourstate_step_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for p,h in json.loads((D/'protocol.json').read_text())['bindings'].items():assert sha(Path(p))==h,p
 rows=json.loads((D/'results.json').read_text())['rows'];assert len(rows)==12;checks=[]
 for a in [2,3,4]:
  group=[r for r in rows if r['address_bits']==a];assert {r['mode'] for r in group}=={'relation_step','truncated_address_negative','old_read_negative','zero_content_negative'}
  for row in group:
   f=D/f'a{a}_{row["mode"]}';log=(f/'yosys.log').read_text();v=(f/'proof.v').read_text();assert 'input[4095:0]physical_memory' in v and 'physical_next[4095:' in v and 'wire pre=(logical_memory==physical_memory[' in v and 'address_defined=&known' in v;assert 'Found and reported 0 problems.' in log
   if row['mode']=='relation_step':assert row['exit_code']==0 and row['proof_passed'] and 'no model found: SUCCESS' in log
   else:assert row['exit_code']==1 and row['proof_failed'] and 'proof did fail' in log
   checks.append({'address_bits':a,'mode':row['mode'],'expected_outcome_verified':True,'bindings':{str(p.relative_to(R)):sha(p) for p in [f/'proof.v',f/'commands.ys',f/'yosys.log']}})
 out={'status':'ALL_3_FULL2048_ROW_FOURVALUE_VECTOR_STEP_PROOFS_AND_9_CONTROLS_VERIFIED','checks':checks,'scope':'Explicit four-value scalar RAM recurrence with fully quantified4096bit physical state vector, lower embedded logical-state precondition and outside-frame preservation. Stable-event/post-settle own-port behavior only; not source macro wiring correspondence, delta ordering or complete design equivalence.'};(D/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
if __name__=='__main__':main()
