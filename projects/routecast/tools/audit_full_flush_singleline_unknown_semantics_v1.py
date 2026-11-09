"""Actual instruction-to-singleLine mapping and procedural-if unknown distinction."""
import json,re,itertools,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];S=R/'experiments/full_source_export_fixed_bus_replay_v19_2026-10-09/reference.v';G=R/'experiments/full_native_ram_gates_v3_2026-10-09/gates.json';B=R/'experiments/full_ram_init_export_runtime_v8_2026-10-09/design.blif';V=R/'experiments/full_csr_counter_preedge_trace_v1_2026-10-09/design.v'
m=max(json.loads(G.read_text())['modules'].values(),key=lambda m:len(m['cells']));bits=m['netnames']['execute_INSTRUCTION']['bits'][15:20];assert bits==[710,712,714,716,718]
assert 'assign dataCache_1_io_cpu_flush_payload_singleLine = (execute_INSTRUCTION[19 : 15] != 5\'h0);' in S.read_text();assert '.names '+' '.join('b'+str(b) for b in bits)+' new_n6607\n00000 1' in B.read_text()
v=V.read_text();assert re.search(r'\.K\(5\),\s*\.LUT_MASK\(32\x27b0{31}1\)\s*\) \\lut_new_n6607',v)
routes=re.findall(r'\.datain\(\\latch_b(\d+)_output_0_0 \),\s*\.dataout\(\\lut_new_n6607_input_0_(\d+) \)',v);assert sorted(int(b) for b,lane in routes)==bits
rows=[];binarymatched=0
for pattern in itertools.product('01x',repeat=5):
 zero='0' if '1' in pattern else ('1' if set(pattern)=={'0'} else 'x');single='1' if zero=='0' else ('0' if zero=='1' else 'x')
 # Isolate source singleLine override with preexisting increment high bit0.
 sourcehigh='1' if single=='1' else '0';gateoverride='0' if zero=='1' else ('1' if zero=='0' else 'x')
 if 'x' not in pattern:assert sourcehigh==gateoverride;binarymatched+=1
 elif sourcehigh!=gateoverride:rows.append({'instruction19_15':''.join(pattern),'source_singleLine':single,'source_if_override_high':sourcehigh,'native_not_zero_override':gateoverride})
assert binarymatched==32 and len(rows)==31
out={'actual_instruction_bits':bits,'export_routes':routes,'binary_patterns_agree':binarymatched,'unknown_pattern_differences':rows,'scope':'Actual zeroInstruction detector and isolated singleLine override semantics with baseline high0. Source procedural if(X) skips, gate complement propagatesX; not full counter D, reachable input history, original/native full functional admission or binary bug.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [S,G,B,V]}}
D=R/'experiments/full_flush_singleline_unknown_semantics_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'binary_agreement':binarymatched,'unknown_differences':len(rows),'example':rows[-1]}))
