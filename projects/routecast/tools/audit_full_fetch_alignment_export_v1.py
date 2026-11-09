"""Bind source fetch mask to native constants and actual exported IBus pins."""
import json,re,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';files=[E/'full_original_unoptimized_proc_state_v1_2026-10-09/source_unoptimized.json',E/'full_ram_mapping_candidate_v1_2026-10-09/structural.json',E/'full_native_ram_gates_v3_2026-10-09/gates.json',E/'full_ram_init_export_runtime_v8_2026-10-09/design.blif',E/'full_native_tag_access_path_trace_v1_2026-10-09/design.v'];records=[]
for label,f in zip(['source_preopt','structural','native'],files[:3]):
 m=max(json.loads(f.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})));bits=m['netnames']['IBusCachedPlugin_fetchPc_pc']['bits'][:2];assert bits==['0','0'];records.append({'stage':label,'fetch_next_pc_low2':bits})
b=files[3].read_text();v=files[4].read_text();assert re.search(r"LUT_K #\(\s*\.K\(5\),\s*\.LUT_MASK\(32'b0{32}\)\s*\) \\lut_const0\s*\(\s*\.in\(5'b0\),\s*\.out\(\\lut_const0_output_0_0 \)",v)
for lane in [0,1]:
 pin=f'iBus_cmd_payload_address[{lane}]';assert '.names const0 '+pin+'\n1 1' in b
 pattern=r'\.datain\(\\lut_const0_output_0_0 \),\s*\.dataout\(\\'+re.escape(pin)+r'_input_0_0 \)';assert re.search(pattern,v)
 assert 'assign \\'+pin+'  = \\'+pin+'_input_0_0 ;' in v
 records.append({'export_pin':pin,'source':'actual lut_const0 mask32zero via exact fpga_interconnect/assign'})
D=E/'full_fetch_alignment_export_v1_2026-10-09';D.mkdir(exist_ok=True);out={'records':records,'conclusion':'Fetch next-PC low2 are literal0 in original preopt/structural/native. Actual exported IBus command low2 pins route from zero-LUT, with BLIF constant-buffer correspondence.','scope':'Exact signal/constant routing audit after combinational settling. Does not prove full fetch address functions, command handshake/scheduler, downstream PC initial states, separate mepc trap capture or global replay admission.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}};(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'records':records,'scope':out['scope']},indent=2))
