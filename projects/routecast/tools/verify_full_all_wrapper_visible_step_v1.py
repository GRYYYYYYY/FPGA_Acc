"""All exact emitted memory top wirings with explicit abstract macro-read relation."""
from pathlib import Path
import json,hashlib,re,subprocess
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_all_wrapper_visible_step_v1_2026-10-09';D.mkdir(exist_ok=False);W=E/'full_ram_mapping_candidate_v1_2026-10-09/wrappers.v';O=E/'emitted_ram_relational_step_v1_2026-10-09/miter.v';P=E/'full_ram_lane_plan_v1_2026-10-09/plan.json';plan=json.load(open(P));text=W.read_text();oracle=O.read_text().split('\nmodule miter(')[0]+'\n';Y=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_Acc/projects/tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys');results=[]
for mi,mem in enumerate(plan['memories']):
 name=f'rc_full_memory_{mi}';a=text.index('module '+name+'(');top=text[a:text.index('endmodule',a)+9];n=len(mem['slices']);w=mem['width'];ports=mem['read_ports'];addr=(mem['size']-1).bit_length();ra_width=ports*addr;qw=ports*w;extra=f'input [{20*n-1}:0] physical,input [{n-1}:0] schedule,output [{n-1}:0] prior_hit,output [{20*n-1}:0] prior_data,';top=top.replace(f'output [{qw-1}:0] Q);',extra+f'output [{qw-1}:0] Q);');assert extra in top
 for si in range(n):
  old=f'.q(q{si}));';assert top.count(old)==1;top=top.replace(old,f'.physical_read(physical[{20*si+19}:{20*si}]),.schedule(schedule[{si}]),.prior_hit(prior_hit[{si}]),.prior_data(prior_data[{20*si+19}:{20*si}]),.q(q{si}));')
 miter=f'''\nmodule miter(input clk,we,input [{ports-1}:0] re,input [{addr-1}:0] wa,input [{ra_width-1}:0] ra,input [{w-1}:0] data,input [{20*n-1}:0] physical,input [{n-1}:0] schedule,output bad,output reg [{qw-1}:0] golden,output [{qw-1}:0] actual);
wire [{n-1}:0] hits;wire [{20*n-1}:0] pending;
{name} dut(.CLK(clk),.WE(we),.RE(re),.WA(wa),.RA(ra),.WD(data),.physical(physical),.schedule(schedule),.prior_hit(hits),.prior_data(pending),.Q(actual));
'''
 for si,sl in enumerate(mem['slices']):
  lo=sl['read_port']*w+sl['start'];hi=sl['read_port']*w+sl['stop']-1;size=sl['stop']-sl['start'];miter+=f'always @(posedge clk) if(re[{sl["read_port"]}]) golden[{hi}:{lo}]<=hits[{si}]?pending[{20*si+size-1}:{20*si}]:physical[{20*si+size-1}:{20*si}];\n'
 miter+='assign bad=golden!=actual; endmodule\n';v=D/f'memory_{mi}.v';ys=D/f'memory_{mi}.ys';log=D/f'memory_{mi}.log';v.write_text(oracle+top+miter);ys.write_text(f'read_verilog {v.name}\nhierarchy -check -top miter\nproc\nflatten\nopt\ncheck -assert\nsat -seq 2 -set-at 1 bad 0 -prove bad 0 -show golden -show actual\n')
 with log.open('w') as out:
  try:code=subprocess.run([str(Y),'-s',ys.name],cwd=D,stdout=out,stderr=subprocess.STDOUT,timeout=15).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 t=log.read_text();ok=code==0 and 'no model found: SUCCESS' in t;results.append({'memory':mem['name'],'read_ports':ports,'visible_bits':qw,'slices':n,'exit_code':code,'sat_success':ok,'counterexample':code==0 and 'model found: FAIL' in t});print(json.dumps(results[-1]),flush=True)
receipt={'results':results,'scope':'All nine exact emitted memory top wirings; exact generic slice state-update with macro read replaced by oracle and pw/er init removed as prior relational lemma. Arbitrary binary prestate with equal visible output at step1 and per-slice logical=applyPending(physical,pending) read premise; independent collision schedules. No macro array/initial-state, delta scheduling, native-export or Full admission.','functional_admission':False,'bindings':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),W,O,P,Y,*D.iterdir()] if f.is_file()}};(D/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
