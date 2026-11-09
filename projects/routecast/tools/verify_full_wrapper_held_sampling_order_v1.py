"""Explicit early/late held sampling relation for audited wrapper selectors."""
import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_wrapper_held_sampling_order_v1_2026-10-09';D.mkdir(exist_ok=True)
inputs=[E/'full_native_wrapper_visible_selectors_v1_2026-10-09/selector_audit.json',E/'full_native_wrapper_state_updates_v1_2026-10-09/state_update_audit.json',E/'full_actual_ram_process_order_v1_2026-10-09/process_order_audit.json']
a=json.loads(inputs[0].read_text());b=json.loads(inputs[1].read_text());assert a['retained_lanes']==a['selector_matches']==174 and b['passed_lane_updates']==174
v='''module held_sampling(input old_er,old_hit,next_er,next_hit,input [19:0] held_old,fwd_old,raw_old,raw_changed,fwd_next,raw_next,output same,output characterization);
wire [19:0] early_sample=old_er ? (old_hit ? fwd_old : raw_old) : held_old;
wire [19:0] late_sample=old_er ? (old_hit ? fwd_old : raw_changed) : held_old;
wire [19:0] early_q=next_er ? (next_hit ? fwd_next : raw_next) : early_sample;
wire [19:0] late_q=next_er ? (next_hit ? fwd_next : raw_next) : late_sample;
assign same=early_q==late_q;
assign characterization=same == (next_er || !old_er || old_hit || raw_old==raw_changed);
endmodule
''';(D/'held_sampling.v').write_text(v)
yosys=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';results=[]
for target,expect in [('characterization','SUCCESS'),('same','FAIL')]:
 p=subprocess.run([str(yosys),'-p',f'read_verilog {D / "held_sampling.v"}; hierarchy -top held_sampling; proc; opt; check -assert; sat -prove {target} 1 -show-inputs -show-outputs'],capture_output=True,text=True,timeout=20);log=p.stdout+p.stderr;(D/(target+'.log')).write_text(log);marker='SAT proof finished - no model found: SUCCESS!' if expect=='SUCCESS' else 'SAT proof finished - model found: FAIL!';assert p.returncode==0 and marker in log;results.append({'target':target,'expected':expect,'exit_code':p.returncode})
out={'results':results,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'miter_sha256':hashlib.sha256(v.encode()).hexdigest(),'premises':['known binary controls/data','early and late held captures differ only by raw changing within active-region observation window','old er/hit/fwd remain constant while held D is sampled; post-edge er/hit/fwd/raw shared between compared schedules'],'conclusion':'Held-capture order is output-independent iff next_er=1 OR old_er=0 OR old_hit=1 OR raw is unchanged. Otherwise there is a symbolic counterexample.','scope':'Conditional scheduler-order model bound to audited selector/update structure, not an actual Full legal bus trace or demonstration that XSIM realizes both schedules. Establishes a missing premise, not source/native inequivalence or physical RAM defect.'};(D/'held_order_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'characterization_passed':True,'unconditional_equality_counterexample':True},indent=2))
