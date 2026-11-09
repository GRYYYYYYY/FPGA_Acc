"""Actual native tag-WE cone and local four-state priority witness."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';f=E/'full_native_ram_gates_v3_2026-10-09/gates.json';rtl=E/'full_source_export_fixed_bus_replay_v19_2026-10-09/reference.v';m=max(json.loads(f.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})))
def driver(b):
 return next((name,c) for name,c in m['cells'].items() if any(b in bs for p,bs in c['connections'].items() if c['port_directions'][p]=='output'))
records=[]
for b,typ in [(3383,'$_DFF_P_'),(3382,'$_OR_'),(8907,'$_MUX_'),(5294,'$_NOT_')]:
 name,c=driver(b);assert c['type']==typ;records.append({'bit':b,'cell':name,'definition':c})
assert records[0]['definition']['connections']=={'C':[254],'D':[3382],'Q':[3383]}
assert records[1]['definition']['connections']=={'A':[8907],'B':[3300],'Y':[3382]}
assert records[2]['definition']['connections']=={'A':[5294],'B':['0'],'S':[7598],'Y':[8907]}
assert records[3]['definition']['connections']=={'A':[2016],'Y':[5294]}
s=rtl.read_text();start=s.index('    tagsWriteCmd_valid = 1\'b0;');end=s.index('\n  end',start);block=s[start:end]
assert block.index('when_DataCache_l850')<block.index('when_DataCache_l1066')<block.index('loader_done')
# Procedural if(X) skips branch. Native mux with different 0/1 branches is X.
witness={'counter_high':'0','override':'x','loader_done':'0','source_flushing_condition':'1','source_tagsWriteCmd_valid':'1','native_not_high':'1','native_mux':'x','native_incoming_write':'x'}
D=E/'full_tag_write_unknown_override_v1_2026-10-09';D.mkdir(exist_ok=True)
out={'actual_native_cone':records,'source_priority_block':block,'local_four_state_witness':witness,'binary_equivalence':'Both reduce to loader_done OR ((!counter_high) AND (!override)) for known binary inputs.','scope':'Local actual-gate/source-priority witness only. Actual earliest trace has pending WEX, but override7598=X at that capture has not yet been directly observed; no claimed complete first-edge origin or binary hardware bug.','next_required_observation':['pre-edge native counter_high2016','pre-edge native override7598','pre-edge native loader_done3300','pre-edge native incoming D3382','matching source priority conditions'],'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [f,rtl]}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'witness':witness,'scope':out['scope']},indent=2))
