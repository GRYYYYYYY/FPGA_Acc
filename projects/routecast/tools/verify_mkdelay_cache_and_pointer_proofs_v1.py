"""Verify exact original state logic, fresh shadow bits and all SAT proof receipts."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';SRC=E/'preserved_source_ram_mapping_v1_2026-10-21/mkDelayWorker32B/preserved_boundary.json';NAMES=['mkdelay_cache_forwarding_sat_v2_2026-10-21','mkdelay_cache_forwarding_sat_v3_2026-10-21','mkdelay_pointer_bound_sat_v4_2026-10-21']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 original=json.loads(SRC.read_text())['modules']['mkDelayWorker32B'];RAM={n:c for n,c in original['cells'].items() if c['type'].endswith('dual_port_ram')};assert len(RAM)==9;oldbits={b for v in original['netnames'].values() for b in v['bits'] if isinstance(b,int)};oldbits|={b for c in original['cells'].values() for bs in c['connections'].values() for b in bs if isinstance(b,int)};verified=[]
 for name in NAMES:
  d=E/name
  for p,h in json.loads((d/'protocol.json').read_text())['bindings'].items():assert sha(Path(p))==h,p
  rows=json.loads((d/'results.json').read_text())['rows'];assert len(rows)==(4 if '_v2_' in name else 6)
  for row in rows:
   f=R/row['folder'];obj=json.loads((f/'proof.json').read_text())['modules']['mkDelayWorker32B'];cut=json.loads((f/'cutpoints.json').read_text());assert {c['cell'] for c in cut}==set(RAM);assert not set(RAM)&set(obj['cells'])
   for n,c in original['cells'].items():
    if n not in RAM:assert obj['cells'][n]==c
   for n,v in original['ports'].items():assert obj['ports'][n]==v
   for n,v in original['netnames'].items():assert obj['netnames'][n]==v
   inputs={b for n,p in obj['ports'].items() if n not in original['ports'] and p['direction']=='input' for b in p['bits']};expected={b for c in RAM.values() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs if isinstance(b,int)};assert inputs==expected
   added={n:c for n,c in obj['cells'].items() if n not in original['cells']};fresh=set()
   for c in added.values():
    for p,bs in c['connections'].items():
     if c['port_directions'][p]=='output':
      for b in bs:assert isinstance(b,int) and b not in oldbits and b not in fresh;fresh.add(b)
   prefix=row['prefix'];target=RAM['dpram1' if prefix=='mesgRF' else 'dpram2'];bits=lambda n:original['netnames'][n]['bits'];assert added['$rc_we']['connections']['D']==target['connections']['we1'];assert added['$rc_data']['connections']['D']==target['connections']['data1'];assert added['$rc_wp']['connections']['D']==bits(prefix+'_rWrPtr')
   for c in added.values():
    if c['type']=='$dff':assert c['connections']['CLK']==target['connections']['clk'] and int(c['parameters']['CLK_POLARITY'],2)==1
   if '_v2_' not in name:
    assert added['$rc_physical_match']['connections']['A']==target['connections']['addr1'] and added['$rc_physical_match']['connections']['B']==target['connections']['addr2'];assert added['$rc_delta']['connections']['A']==bits(prefix+'_rWrPtr') and added['$rc_delta']['connections']['B']==bits(prefix+'_rRdPtr');assert len(added['$rc_delta']['connections']['Y'])==11;assert int(''.join(reversed(added['$rc_bound']['connections']['B'])),2)==512
   commands=(f/'commands.ys').read_text();log=(f/'yosys.log').read_text();assert '-ignore_unknown_cells' not in commands and '-seq 2' in commands and '-prove-skip 1' in commands;assert 'Found and reported 0 problems.' in log
   positive=row['mode'] in ['forwarding','bounded_collision','reset_base','induction']
   if positive:assert row['exit_code']==0 and row['proof_passed'] and 'no model found: SUCCESS' in log
   else:assert row['exit_code']==1 and row['proof_failed'] and 'proof did fail' in log
   if row['mode']=='reset_base':assert '-set wciS0_MReset_n 0' in commands
   if row['mode']=='induction':assert '-set wciS0_MReset_n 1 -set-at 1 rc_bound 1' in commands
   verified.append({'study':name,'prefix':prefix,'mode':row['mode'],'expected_outcome_verified':True,'bindings':{str(p.relative_to(R)):sha(p) for p in [f/'proof.json',f/'commands.ys',f/'yosys.log']}})
 out={'status':'ACTUAL_BINARY_SOURCE_POINTER_INVARIANTS_AND_CACHE_FORWARDING_VERIFIED','proof_receipts':verified,'retained_source_state_logic_exact':True,'pointer_invariants':'Both11bit modular occupancies<=512 hold after reset and are inductive under actual source transition with arbitrary binary RAM output cutpoints.','cache_claim':'For each actual transaction getter, one-edge write+physical10bit collision+occupancy<=512 forwards captured write data independent of RAM outputs. Full11bit pointer-match forwarding separately checked.','scope':'Binary source transition system with explicit opaque RAM-output cutpoints, deasserted reset for cache lemma, source reset base for pointer invariant. No arbitrary four-state or full-source equivalence. Source prevent_hanging_nodes path and complete memory correspondence remain separate obligations.'};d=E/NAMES[-1];(d/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
if __name__=='__main__':main()
