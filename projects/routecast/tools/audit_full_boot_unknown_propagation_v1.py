"""Compose actual frozen preedges from boot counter through IBus controls/data/address."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_boot_unknown_propagation_v1_2026-10-09';D.mkdir(exist_ok=True)
paths={
 'boot':'full_flusher_boot_full_preedge_trace_v1_2026-10-09/trace_audit.json',
 'capture':'full_ibus_ready_control_preedge_trace_v1_2026-10-09/trace_audit.json',
 'ready':'full_ibus_ready_preedge_trace_v1_2026-10-09/trace_audit.json',
 'bank':'full_ibus_bank_history_preedge_trace_v1_2026-10-09/trace_audit.json',
 'write':'full_ibus_write_history_preedge_trace_v1_2026-10-09/trace_audit.json',
 'fill':'full_ibus_fill_capture_preedge_trace_v1_2026-10-09/trace_audit.json'}
reports={};files=[]
for name,rel in paths.items():
 f=R/'experiments'/rel;files.append(f);a=json.loads(f.read_text());assert a['cycles']==512 and a['replay_fidelity'] and a['mismatches']==42370;reports[name]=a
boot=reports['boot']['rows'];assert boot[3]['reset']=='0' and boot[3]['native_Q']=='0'*8 and boot[3]['native_start']=='1' and boot[3]['native_D']=='0'+'x'*7
assert boot[3]['src_singleLine']=='x' and boot[3]['native_instruction']=='x'*5 and boot[3]['native_lineId']=='x'*7
assert boot[4]['native_Q']=='0'+'x'*7 and boot[4]['src_counter']=='0'*8 and boot[5]['native_Q']=='x'*8
c=reports['capture']['rows'][5];assert c['control_pins']=='1x001' and c['new_n6108']=='x' and c['native_mmu_state']=='000'
r=reports['ready']['rows'][5];assert r['native_ready']=='x' and r['src_ready']=='0' and r['src_busy']=='0'
b=reports['bank']['rows'][6];assert b['native_er']=='x' and b['native_held']==b['native_data']=='x'*32
f=reports['fill']['source_capture_rows'][0];assert f['cycle']==135 and f['src_payload']=='0'*7 and f['native_capture']=='x' and f['native_payload']=='x'*7
w=reports['write']['write_address_differences'][0];assert w['cycle']==137 and w['source_wa']=='0'*10 and w['native_wa']=='x'*7+'000'
out={'original_full_mismatches':42370,'first_counter_difference_cycle':4,'boot_sampling_cycle':3,'events':[{'cycle':3,'event':'Released reset with start1 samples instruction/lineId unknown; actual native counter D0xxxxxxx.'},{'cycle':4,'event':'Actual native counter Q0xxxxxxx, originalQ0; nativeDxxxxxxxx.'},{'cycle':5,'event':'Actual counterQxxxxxxxx; capture6108X propagates through otherwiseknown control6085 and early ready masks.'},{'cycle':6,'event':'Actual bank erX and held/data32X; actual LUT held path preservesunknown.'},{'cycle':135,'event':'First original knownfillcapture with payload0; nativefillcapture/inputaddress bothX.'},{'cycle':137,'event':'First original knownwrite address0; nativeupper7writeaddressX.'}],'scope':'Composed named full frozen replay observations and separately bound local LUT/register paths. Earliest counter difference, not earliest all-design/output difference; no claim all42370 mismatches have thiscause. No changedRTL/stimulus/init or functional admission.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['hashes','events']},indent=2))
