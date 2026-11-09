"""Original boot flush reads unreset execute instruction/RS1 state."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_flusher_boot_input_contract_v1_2026-10-09';D.mkdir(exist_ok=True)
S=R/'experiments/full_source_export_fixed_bus_replay_v19_2026-10-09/reference.v';text=S.read_text();records={};files=[S]
assert "assign dataCache_1_io_cpu_flush_payload_singleLine = (execute_INSTRUCTION[19 : 15] != 5'h0);" in text
assert 'assign _zz_io_cpu_flush_payload_lineId_1 = (execute_RS1 >>> 5);' in text
block='\n'.join(text.splitlines()[7423:7430]);assert 'if(stageB_flusher_start)' in block and 'io_cpu_execute_isValid' not in block
for label,rel in [('source','full_original_unoptimized_proc_state_v1_2026-10-09/source_unoptimized.json'),('native','full_native_ram_gates_v3_2026-10-09/gates.json')]:
 f=R/'experiments'/rel;files.append(f);m=max(json.loads(f.read_text())['modules'].values(),key=lambda x:len(x['cells']));line=m['netnames']['dataCache_1.io_cpu_flush_payload_lineId']['bits'];items=[]
 if label=='native':assert line==m['netnames']['execute_RS1']['bits'][5:12]
 else:
  shift=next(c for c in m['cells'].values() if c['connections'].get('Y',[])[:7]==line);assert shift['type']=='$sshr' and shift['connections']['A']==m['netnames']['execute_RS1']['bits'];assert int(''.join(reversed(shift['connections']['B'])),2)==5
 for signal,lanes in [('execute_INSTRUCTION',range(15,20)),('execute_RS1',range(5,12))]:
  for lane in lanes:
   b=m['netnames'][signal]['bits'][lane];matches=[(k,c) for k,c in m['cells'].items() if b in c['connections'].get('Q',[])];assert len(matches)==1;k,c=matches[0];assert c['type']==('$dff' if label=='source' else '$_DFF_P_');assert not any('init' in v.get('attributes',{}) for v in m['netnames'].values() if b in v['bits']);items.append({'signal':signal,'lane':lane,'Q':b,'cell':k,'definition':c})
 q=m['netnames']['dataCache_1.stageB_flusher_start']['bits'][0];c=next(c for c in m['cells'].values() if q in c['connections'].get('Q',[]));assert (c['parameters']['ARST_VALUE']=='1') if label=='source' else (c['type']=='$_DFF_PP1_');records[label]={'unreset_boot_inputs':items,'start_reset_register':c,'lineId_bits':line}
out={'records':records,'original_boot_block':block,'conclusion':'Boot start is reset1 and original counter start branch samples singleLine/lineId without execute-valid guard. SingleLine depends on five actual unreset instruction lanes; lineId depends on seven actual unreset RS1 lanes in both representations. Known reset counter/start does not establish those inputs or their equality.','scope':'Original RTL/state inventory; no proposed reset change, arbitrary shared initial assignment or claim allbinaryhardware executions fail. Actual input history awaits live full boot trace.','hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print('PASS12unresetbootinputlanes/source-and-native;startreset1')
