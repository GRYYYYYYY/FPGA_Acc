"""Conditional two-sided read-order lemma, bound to actual tag pin/capture checks."""
import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_tag_valid_nonhit_raw_order_v1_2026-10-09';D.mkdir(exist_ok=True)
files=[E/'full_structural_native_datacache_tag_macro_inputs_v3_2026-10-09/condition_audit.json',E/'full_structural_native_datacache_tag_capture_bridge_v1_2026-10-09/condition_audit.json',E/'full_actual_ram_process_order_v1_2026-10-09/process_order_audit.json']
pin,capture,order=[json.loads(f.read_text()) for f in files]
assert pin['success'] and capture['success'] and not pin['constant_premises']
assert all(r['observed_marker'].endswith('SUCCESS!') for r in order['results'] if r['target'] in ['characterization','visible_same'])
# Actual WE2=0 and real tag lanes are retained in pin checks.
for i in [0,1]:
 rows=[r for r in pin['positions'] if r['name']==f'dataCache_1.ways_0_tags.s{i}.ram.we2[0]'];assert len(rows)==1 and rows[0]['structural']==rows[0]['native']=='0'
v='''module read_order(input re,pw,order_s,order_n,input [9:0] wa_s,wa_n,ra_s,ra_n,input [21:0] pd_s,pd_n,old_s,old_n,output bad,missing_array_bad);
wire pins_ok=(!pw || ((wa_s==wa_n)&&(pd_s==pd_n))) && (!re || (ra_s==ra_n));
wire array_at_read_ok=!re || (old_s==old_n);
wire hit_s=pw && wa_s==ra_s;
wire hit_n=pw && wa_n==ra_n;
wire [21:0] raw_s=(order_s && hit_s) ? pd_s : old_s;
wire [21:0] raw_n=(order_n && hit_n) ? pd_n : old_n;
wire observed_bad=re && !hit_s && (raw_s!=raw_n);
assign bad=pins_ok && array_at_read_ok && observed_bad;
assign missing_array_bad=pins_ok && observed_bad;
endmodule
'''
(D/'read_order.v').write_text(v)
y=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';results={}
for target,marker in [('bad','SAT proof finished - no model found: SUCCESS!'),('missing_array_bad','SAT proof finished - model found: FAIL!')]:
 r=subprocess.run([str(y),'-p',f'read_verilog read_order.v; prep -top read_order; sat -prove {target} 0 -show-inputs -show-outputs'],cwd=D,capture_output=True,text=True,timeout=30)
 log=r.stdout+r.stderr;(D/(target+'.log')).write_text(log);assert r.returncode==0 and marker in log
 results[target]={'exit_code':r.returncode,'marker':marker,'log_sha256':hashlib.sha256(log.encode()).hexdigest()}
out={'results':results,'bindings':{'slices':2,'logical_lanes':[20,2],'we2':'0','pin_bridge_success':True,'qualified_hit_capture_success':True},'premises':['known binary edge/control/address/data','shared pending write enable; pending address/data equal when enabled','read addresses equal when actual read enable asserted','pre-edge arrays equal at selected valid read address; this remains an explicit unproved array relation','hit captures same-edge pending write collision and er captures actual read enable','order_s/order_n independently arbitrary port write-first/read-first choices'], 'conclusion':'Post-edge raw read values agree whenever actual next er=1 and next hit=0, regardless independent macro process order. Missing pre-edge read-array equality produces counterexample.','scope':'Conditional order lemma over22 logical tag data bits, tied to prior actual pin/capture/primitive artifacts. Does not establish initial arrays, global current-state premises, held active-region sampling, X events or Full replay equivalence.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'miter_sha256':hashlib.sha256(v.encode()).hexdigest()}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'results':results,'conclusion':out['conclusion'],'scope':out['scope']},indent=2))
