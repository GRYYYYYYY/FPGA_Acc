"""Bind three actual debug-FSM export registers to proven idle D cones."""
import json,re,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_csr_counter_preedge_trace_v1_2026-10-09';V=D/'design.v';P=D/'primitives.v';T=D/'tb.v';v=V.read_text();p=P.read_text();tb=T.read_text();records=[]
for d,q in [(3386,3387),(3406,3407),(3408,3409)]:
 target='$_DFF_PP0__b'+str(q);routes={}
 assert re.search(r'\\\$_DFF_PP0_\s*#\(\s*\) \\'+re.escape(target)+r'\s*\(',v)
 for port,source,suffix in [('D','lut_b'+str(d)+'_output_0_0','input_0_0'),('C','clk_output_0_0','clock_0_0'),('R','reset_output_0_0','input_1_0')]:
  dest=target+'_'+suffix;assert re.search(r'\.datain\(\\'+re.escape(source)+r' \),\s*\.dataout\(\\'+re.escape(dest)+r' \)',v);assert '.'+port+'(\\'+dest+' )' in v;routes[port]={'source':source,'pin':dest}
 assert '.Q(\\'+target+'_output_0_0 )' in v;records.append({'register':target,'routes':routes,'Q':target+'_output_0_0'})
assert 'module \\$_DFF_PP0_ (input C,D,R, output reg Q);\n always @(posedge C or posedge R) if (R) Q <= 1\'b0; else Q <= D;' in p
assert 'assign dataout = datain;' in p
for top in ['clk','reset','debug_bus_cmd_valid']:assert re.search(r'assign \\'+top+r'_output_0_0\s*=\s*\\'+top+r'\s*;',v)
assert re.findall(r'\bdebug_bus_cmd_valid\s*(?:=|<=)\s*([^;]+);',tb)==['0']
assert 'reg [0:0] reset=0;' in tb and 'initial begin reset=1;debugReset=1;#1;' in tb
assert '#4;clk=0;if(i==2) begin reset=0;debugReset=0;end' in tb
assert '$sdf_annotate' not in tb
files=[R/'experiments/full_debug_idle_blif_unknown_v1_2026-10-09/audit.json',R/'experiments/full_debug_idle_export_luts_v1_2026-10-09/audit.json',V,P,T]
a=json.loads(files[0].read_text());assert list(a['trials'][0]['roots'].values())==['0','0','0','1']
export=json.loads(files[1].read_text());assert export['checked_functions']==63 and len(export['verified_top_buffers'])==10
out={'registers':records,'conditions':'Actual shared reset rises from0to1 before settled startup comparison; subsequent shared clock edges, reset deasserts aftercycle2; debugcmdValid stays0. No SDF annotation in tb.','conclusion':'Three real exported reset-zero registers consume the previously verified idle-zero D functions. After known reset and settling, idle preservation follows despite unknown other state boundaries. This is a composed logic/primitive proof, not a new direct FSM trace observation.','scope':'Local debug FSM/override state-zero relation only. No cache payload/other state admission, timing-backannotated hardware claim or resolution of42370 full replay differences.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
O=R/'experiments/full_debug_idle_export_registers_v1_2026-10-09';O.mkdir(exist_ok=True);(O/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'registers':len(records),'conclusion':out['conclusion']},indent=2))
