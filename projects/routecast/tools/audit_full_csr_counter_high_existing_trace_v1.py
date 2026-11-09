"""Actual early high-D telemetry and divergent registered high state."""
import re,json,itertools,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_csr_capture_operands_trace_v1_2026-10-09';v=(D/'design.v').read_text();log=(D/'control.log').read_text();mapping=R/'experiments/full_source_export_data_flush_counter_trace_v16_2026-10-09/counter_high_pin_mapping.json';mp=json.loads(mapping.read_text());mask=mp['mask'];assert '.LUT_MASK(32\'b'+mask+')' in v
for p in mp['pins']:assert '.datain('+p['source']+' ),\n        .dataout('+p['target']+' )' in v
rx=r'COUNTER_CONTROL cycle=\s*(\d+) src_singleLine=([01x]) src_instruction=([0-9a-fx]+) src_hold=([01x]) src_start=([01x]) exp_highD=([01x]) exp_zeroInstruction=([01x]) exp_Dinputs=([01x]{5})'
rows=[]
for c,s,i,h,start,d,z,pins in re.findall(rx,log):
 possible={mask[-1-sum(int(b)<<lane for lane,b in enumerate(bs))] for bs in itertools.product(*[['0','1'] if b=='x' else [b] for b in pins])};pred=next(iter(possible)) if len(possible)==1 else 'x';assert pred==d;rows.append({'cycle':int(c),'source_singleLine':s,'source_counter_start':start,'source_hold':h,'native_D':d,'native_zero_instruction':z,'native_D_pin_values_lsb_first':pins})
assert len(rows)==141 and rows[3]['native_D']=='x'
source={int(c):counter for c,counter in re.findall(r'DATA_FLUSH cycle=\s*(\d+) src_counter=([0-9a-fx]+)',log)}
high={int(c):val for c,val in re.findall(r'PIPE_BOUNDARY cycle=\s*(\d+) index=1 value=([01x])',log)}
assert source[3]=='00' and source[4]=='01' and high[3]=='0' and high[4]=='x'
out={'matched_high_D_rows':len(rows),'early_rows':rows[:6],'cycle4_source_counter':source[4],'cycle4_native_high':high[4],'conclusion':'Actual post-edge3 highD isX with start0/high0/unknown zeroInstruction. Actual post-edge4 source counter01 has high0 but native highX, feeding previously verified cycle5 CSRcaptureX path.','scope':'HighD telemetry is post-edge, not a new pre-edge sample of clock4; no all42370 cause or binary hardware bug claimed. Need event-stable/preedge D evidence to close exact sampled transition.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [D/'control.log',D/'design.v',mapping]}}
O=R/'experiments/full_csr_counter_high_existing_trace_v1_2026-10-09';O.mkdir(exist_ok=True);(O/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'matched':len(rows),'cycle3':rows[3],'sourcecounter4':source[4],'nativehigh4':high[4]}))
