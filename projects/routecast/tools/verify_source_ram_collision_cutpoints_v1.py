"""Verify exact local abstraction and concrete SAT witness aliases."""
import json,hashlib
from pathlib import Path
from audit_source_ram_collision_cutpoints_v1 import COMB
R=Path(__file__).resolve().parents[1];D=R/'experiments/source_ram_collision_cutpoints_v1_2026-10-21';P=R/'experiments/preroute_family_admission_v1_2026-10-20/structure_preflight_v5'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for p,h in json.loads((D/'protocol.json').read_text())['bindings'].items():assert sha(Path(p))==h,p
 rows=json.loads((D/'results.json').read_text())['rows'];assert len(rows)==16;verified=[]
 for row in rows:
  f=R/row['folder'];source=json.loads((P/row['family']/'proc.json').read_text())['modules'][row['parent_module']];obj=json.loads((f/'cutpoint.json').read_text())['modules']['cutpoint'];ram=source['cells'][row['ram_cell']];cut=json.loads((f/'cutpoints.json').read_text());expected={n:c for n,c in source['cells'].items() if c['type'] not in COMB};assert {c['cell'] for c in cut}==set(expected)
  for n,c in source['cells'].items():
   if c['type'] in COMB:assert obj['cells'][n]==c
   else:assert n not in obj['cells']
  assert set(obj['cells'])=={n for n,c in source['cells'].items() if c['type'] in COMB}|{'$rc_equal','$rc_collision'}
  free={b for p in source['ports'].values() if p['direction']=='input' for b in p['bits'] if isinstance(b,int)}
  for c in expected.values():free.update(b for k,bs in c['connections'].items() if c['port_directions'][k]=='output' for b in bs if isinstance(b,int))
  assert {b for p in obj['ports'].values() if p['direction']=='input' for b in p['bits']}==free
  assert obj['cells']['$rc_equal']['connections']['A']==ram['connections']['addr1'];assert obj['cells']['$rc_equal']['connections']['B']==ram['connections']['addr2'];assert obj['cells']['$rc_collision']['connections']['B']==ram['connections']['we1']
  assert row['exit_code']==0 and row['status']=='CUTPOINT_COLLISION_POSSIBLE_NOT_REACHABILITY';log=(f/'yosys.log').read_text();assert 'model found: FAIL!' in log and 'Found and reported 0 problems.' in log
  signals=json.loads((f/'witness.json').read_text())['signal'];values={s['name']:(int(s['data'][0],2) if 'data' in s else int(s['wave'][0])) for s in signals};assert values['rc_collision']==values['rc_we1']==1 and values['rc_addr1']==values['rc_addr2']
  verified.append({'family':row['family'],'parent_module':row['parent_module'],'ram_cell':row['ram_cell'],'witness_address':values['rc_addr1'],'bindings':{str(p.relative_to(R)):sha(p) for p in [f/'cutpoint.json',f/'cutpoints.json',f/'commands.ys',f/'yosys.log',f/'witness.json']}})
 out={'status':'ALL_16_LOCAL_COLLISION_CUTPOINT_WITNESSES_VERIFIED','rows':verified,'reachable_collisions_proven':False,'collision_free_exclusions_proven':0,'note':'All noncombinational outputs are independent cutpoints. Binary SAT possible states do not establish source reset reachability or observable collision damage. No ignored unsupported cells or source clock/reset conversion.'};(D/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
if __name__=='__main__':main()
