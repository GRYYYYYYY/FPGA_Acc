"""Actual original trap selection under proven interrupt privilege guard."""
import json,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];src=R/'experiments/full_original_unoptimized_proc_state_v1_2026-10-09/source_unoptimized.json'
m=max(json.loads(src.read_text())['modules'].values(),key=lambda m:len(m['cells']))
net=lambda n:m['netnames'][n]['bits']
v=net('CsrPlugin_interrupt_valid');p=net('CsrPlugin_interrupt_targetPrivilege')
roots=net('when_CsrPlugin_l1310')+net('when_CsrPlugin_l1318')+[13645]
assert m['cells']['$procmux$2473']['connections']['S']==[13645]
assert m['cells']['$procmux$2473']['connections']['B']==net('writeBack_PC')
drivers={b:(k,c) for k,c in m['cells'].items() for port,bs in c['connections'].items() if c['port_directions'][port]=='output' for b in bs if isinstance(b,int)}
cells={};leaves=set(v+p)
def visit(b):
 if not isinstance(b,int):return
 if b not in drivers:leaves.add(b);return
 k,c=drivers[b]
 if 'ff' in c['type'].lower() or 'mem' in c['type'].lower():leaves.add(b);return
 if k in cells:return
 cells[k]=c
 for port,bs in c['connections'].items():
  if c['port_directions'][port]=='input':
   for x in bs:visit(x)
for b in roots:visit(b)
others=sorted(leaves-set(v+p));ports={'valid':{'direction':'input','bits':v},'priv':{'direction':'input','bits':p},'other':{'direction':'input','bits':others},'roots':{'direction':'output','bits':roots}}
D=R/'experiments/full_trap_privilege_selection_v1_2026-10-09';D.mkdir(exist_ok=True)
(D/'cut.json').write_text(json.dumps({'modules':{'actual_cut':{'attributes':{},'ports':ports,'cells':cells,'netnames':{}}}},indent=2)+'\n')
(D/'miter.v').write_text('module miter(input valid,input [1:0] priv,input ['+str(len(others)-1)+':0] other,output bad,missing_guard_bad);wire [2:0] r;actual_cut u(.valid(valid),.priv(priv),.other(other),.roots(r));assign missing_guard_bad=r[0] && !(r[1] && r[2]);assign bad=(!valid || priv==2\'b11) && missing_guard_bad;endmodule\n')
y=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';results={}
for target,expected in [('bad',True),('missing_guard_bad',False)]:
 c=subprocess.run([str(y),'-p',f'read_json cut.json; read_verilog miter.v; prep -top miter; flatten; sat -prove {target} 0 -show-inputs -show-outputs'],cwd=D,capture_output=True,text=True,timeout=30)
 log=c.stdout+c.stderr;(D/(target+'.log')).write_text(log);ok='SAT proof finished - no model found: SUCCESS!' in log
 assert c.returncode==0 and ok==expected
 if not ok:assert 'SAT proof finished - model found: FAIL!' in log
 results[target]={'exit_code':c.returncode,'proof_success':ok}
guard=R/'experiments/full_interrupt_privilege_guard_v1_2026-10-09/audit.json';assert json.loads(guard.read_text())['results']['missing_base_bad']['proof_success']
out={'results':results,'cells':len(cells),'boundary_bits':len(leaves),'roots':roots,'actual_trap_pc_mux':m['cells']['$procmux$2473'],'guard_evidence':str(guard.relative_to(R)),'conclusion':'Under original interrupt_valid=>interrupt_targetPrivilege11, trap outer enable implies actual debug guard and targetPrivilege==11. Thus original inner trap selection can be removed in binary reset-established states. Without capture guard, actual counterexample exists.','scope':'Actual original selection cone only. Does not compare native outer enable, software CSR write priority, complete mepc D, four-state events or global replay.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [src,guard,D/'cut.json',D/'miter.v',D/'bad.log',D/'missing_guard_bad.log']}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'results':results,'cells':len(cells),'boundary_bits':len(leaves),'conclusion':out['conclusion']},indent=2))
