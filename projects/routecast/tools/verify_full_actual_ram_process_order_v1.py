"""Two legal process orders for actual blocking dual-port RAM, we2=0."""
import hashlib,json,re,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';F=E/'full_source_export_fixed_bus_replay_v19_2026-10-09/primitives.v';D=E/'full_actual_ram_process_order_v1_2026-10-09';D.mkdir(exist_ok=True)
s=F.read_text();macro=re.search(r'module dual_port_ram\s*#\(.*?endmodule',s,re.S)[0];macro=re.sub(r'\s*specify.*?endspecify','',macro,flags=re.S)
normalized=re.sub(r'//[^\n]*','',macro);normalized=re.sub(r'\s+',' ',normalized)
assert 'always@(posedge clock) begin if(we1) begin Mem[addr1] = data1; end out1 = Mem[addr1]; end' in normalized
assert 'always@(posedge clock) begin if(we2) begin Mem[addr2] = data2; end out2 = Mem[addr2]; end' in normalized
(D/'actual_macro.v').write_text(macro+'\n')
verilog='''module order_miter(input [9:0] wa,ra,input [19:0] old_read,new_data,input we,output same,output characterization);
wire collision=we && (wa==ra);
wire [19:0] port1_then_port2=collision ? new_data : old_read;
wire [19:0] port2_then_port1=old_read;
assign same=(port1_then_port2==port2_then_port1);
assign characterization=(same==(!collision || old_read==new_data));
endmodule
''';(D/'order_miter.v').write_text(verilog)
yosys=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';results=[]
for target,expected in [('characterization','SUCCESS'),('same','FAIL')]:
 cmd=[str(yosys),'-p',f'read_verilog {D / "order_miter.v"}; hierarchy -top order_miter; proc; opt; check -assert; sat -prove {target} 1 -show-inputs -show-outputs'];p=subprocess.run(cmd,capture_output=True,text=True,timeout=20);log=p.stdout+p.stderr;(D/(target+'.log')).write_text(log)
 marker='SAT proof finished - no model found: SUCCESS!' if expected=='SUCCESS' else 'SAT proof finished - model found: FAIL!';assert p.returncode==0 and marker in log
 results.append({'target':target,'expected':expected,'exit_code':p.returncode,'observed_marker':marker})
visible="""module visible_order(input [9:0] wa,ra,input [19:0] old_read,new_data,held,input we,er,output same,output no_forward_same);
wire hit=we && (wa==ra);
wire [19:0] raw_a=hit ? new_data : old_read;
wire [19:0] raw_b=old_read;
wire [19:0] q_a=er ? (hit ? new_data : raw_a) : held;
wire [19:0] q_b=er ? (hit ? new_data : raw_b) : held;
assign same=q_a==q_b;
assign no_forward_same=q_a==(er ? raw_b : held);
endmodule
"""
(D/'visible_order.v').write_text(visible)
for target,expected in [('same','SUCCESS'),('no_forward_same','FAIL')]:
 p=subprocess.run([str(yosys),'-p',f'read_verilog {D / "visible_order.v"}; hierarchy -top visible_order; proc; opt; check -assert; sat -prove {target} 1 -show-inputs -show-outputs'],capture_output=True,text=True,timeout=20)
 log=p.stdout+p.stderr;(D/('visible_'+target+'.log')).write_text(log)
 marker='SAT proof finished - no model found: SUCCESS!' if expected=='SUCCESS' else 'SAT proof finished - model found: FAIL!';assert p.returncode==0 and marker in log
 results.append({'target':'visible_'+target,'expected':expected,'exit_code':p.returncode,'observed_marker':marker})
out={'actual_macro_sha256':hashlib.sha256(macro.encode()).hexdigest(),'input_sha256':hashlib.sha256(F.read_bytes()).hexdigest(),'miter_sha256':hashlib.sha256(verilog.encode()).hexdigest(),'results':results,'premises':['we2=0, as all actual macro pins were audited','known binary clock/addresses/data/write enable','both positive-clock processes execute once in same active region; considered port1-first and port2-first','old_read denotes Mem at read address before the edge'],'visible_relation':'Under shared held value, hit equals the same-edge collision and fwd equals new_data, two-mux visible q masks either raw process order; removing forwarding gives a counterexample. Does not prove held sampling or these state relations globally.', 'conclusion':'out2 is order-independent iff no enabled same-address collision or old_read equals new_data. Unconditional order equality has an actual symbolic counterexample.','scope':'Local actual primitive process-order characterization only. Wrapper forwarding may mask this raw difference; no Full external counterexample or physical RAM claim. Does not prove X-enable/address behavior or simulator always selects both orders.'};(D/'process_order_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'characterization_proved':True,'unconditional_same_counterexample':True},indent=2))
