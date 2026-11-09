"""Pointwise tag array relation preservation; does not assume zero initialization."""
import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_tag_array_commit_relation_v1_2026-10-09';D.mkdir(exist_ok=True)
files=[E/'full_structural_native_datacache_tag_macro_inputs_v3_2026-10-09/condition_audit.json',E/'full_actual_ram_process_order_v1_2026-10-09/actual_macro.v']
a=json.loads(files[0].read_text());assert a['success'] and not a['constant_premises']
macro=files[1].read_text();assert 'Mem[addr1] = data1;' in macro and 'Mem[addr2] = data2;' in macro and 'initial' not in macro
for i in [0,1]:
 r=next(r for r in a['positions'] if r['name']==f'dataCache_1.ways_0_tags.s{i}.ram.we2[0]');assert r['structural']==r['native']=='0'
v='''module commit_relation(input pw,known_equal,input [9:0] probe,wa_s,wa_n,input [21:0] old_s,old_n,pd_s,pd_n,output preservation_bad,missing_data_bad,missing_base_bad,recovery_bad);
wire addresses_ok=!pw || wa_s==wa_n;
wire data_ok=!pw || pd_s==pd_n;
wire old_ok=old_s==old_n;
wire [21:0] next_s=(pw && wa_s==probe) ? pd_s : old_s;
wire [21:0] next_n=(pw && wa_n==probe) ? pd_n : old_n;
wire known_next=known_equal || (pw && wa_s==probe);
assign recovery_bad=addresses_ok && data_ok && (!known_equal || old_ok) && known_next && (next_s!=next_n);
assign preservation_bad=addresses_ok && data_ok && old_ok && (next_s!=next_n);
assign missing_data_bad=addresses_ok && old_ok && (next_s!=next_n);
assign missing_base_bad=addresses_ok && data_ok && (next_s!=next_n);
endmodule
'''
(D/'commit_relation.v').write_text(v)
y=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';results={}
for target,success in [('recovery_bad',True),('preservation_bad',True),('missing_data_bad',False),('missing_base_bad',False)]:
 r=subprocess.run([str(y),'-p',f'read_verilog commit_relation.v; prep -top commit_relation; sat -prove {target} 0 -show-inputs -show-outputs'],cwd=D,capture_output=True,text=True,timeout=30)
 log=r.stdout+r.stderr;(D/(target+'.log')).write_text(log)
 marker='SAT proof finished - no model found: SUCCESS!' if success else 'SAT proof finished - model found: FAIL!'
 assert r.returncode==0 and marker in log
 results[target]={'exit_code':r.returncode,'marker':marker,'log_sha256':hashlib.sha256(log.encode()).hexdigest()}
out={'results':results,'probe_width':10,'logical_tag_data_bits':22,'slices':[20,2],'premises':['shared known binary pending enable','enabled write addresses/data correspond','old arrays correspond pointwise at arbitrary probe','actual second write port disabled'], 'conclusion':'For an arbitrary address, enabled pending commit preserves paired old-array equality under matched write pins. Universal pointwise relation is therefore conditionally preserved.','overwrite_recovery':'A shared per-address known-equal marker initially0 needs no initial array equality. A matched write at that address sets marker1 and establishes equality; conditional preservation holds for every marked address. Does not establish that required read addresses have been written.', 'initialization_status':'Actual primitive Mem has no initial block. Unconstrained independent binary arrays need not correspond; missing_base_bad supplies counterexample even with matching write pins. No zero initialization or known equal initial memory is established. Shared arbitrary initial content is a possible coupling premise, not evidence of actual initial equality.','scope':'Symbolic pointwise one-edge preservation bound to actual tag pin proof/primitive update. Does not discharge base, global state/enable histories, raw-output schedule, held sampling or Full replay.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'miter_sha256':hashlib.sha256(v.encode()).hexdigest()}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'results':results,'overwrite_recovery':'A shared per-address known-equal marker initially0 needs no initial array equality. A matched write at that address sets marker1 and establishes equality; conditional preservation holds for every marked address. Does not establish that required read addresses have been written.', 'initialization_status':out['initialization_status']},indent=2))
