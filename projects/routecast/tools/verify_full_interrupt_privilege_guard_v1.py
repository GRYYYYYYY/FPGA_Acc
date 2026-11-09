"""Actual original interrupt-valid implies captured privilege: binary induction."""
import json,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];src=R/'experiments/full_original_unoptimized_proc_state_v1_2026-10-09/source_unoptimized.json'
m=max(json.loads(src.read_text())['modules'].values(),key=lambda m:len(m['cells']))
net=lambda n:m['netnames'][n]['bits']
v=net('CsrPlugin_interrupt_valid');p=net('CsrPlugin_interrupt_targetPrivilege')
def reg(q):return next(c for c in m['cells'].values() if c['connections'].get('Q')==q)
vr,pr=reg(v),reg(p)
assert vr['type']=='$adff' and vr['parameters']['ARST_VALUE']=='0' and vr['connections']['ARST']==[255]
assert pr['type']=='$dff'
roots=vr['connections']['D']+pr['connections']['D']
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
others=sorted(leaves-set(v+p));ports={'valid':{'direction':'input','bits':v},'priv':{'direction':'input','bits':p},'other':{'direction':'input','bits':others},'next':{'direction':'output','bits':roots}}
D=R/'experiments/full_interrupt_privilege_guard_v1_2026-10-09';D.mkdir(exist_ok=True)
(D/'cut.json').write_text(json.dumps({'modules':{'actual_cut':{'attributes':{},'ports':ports,'cells':cells,'netnames':{}}}},indent=2)+'\n')
(D/'miter.v').write_text('module miter(input valid,input [1:0] priv,input ['+str(len(others)-1)+':0] other, output bad,missing_base_bad,inverted_privilege_bad);wire [2:0] n;actual_cut u(.valid(valid),.priv(priv),.other(other),.next(n));assign missing_base_bad=n[0] && n[2:1]!=2\'b11;assign bad=(!valid || priv==2\'b11) && missing_base_bad;assign inverted_privilege_bad=n[0] && ((n[2:1] ^ 2\'b01)!=2\'b11);endmodule\n')
y=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';results={}
for target in ['bad','missing_base_bad','inverted_privilege_bad']:
 c=subprocess.run([str(y),'-p',f'read_json cut.json; read_verilog miter.v; prep -top miter; flatten; sat -prove {target} 0 -show-inputs -show-outputs'],cwd=D,capture_output=True,text=True,timeout=30)
 log=c.stdout+c.stderr;(D/(target+'.log')).write_text(log)
 assert c.returncode==0
 ok='SAT proof finished - no model found: SUCCESS!' in log
 if target in ['bad','missing_base_bad']:assert ok
 if target=='inverted_privilege_bad':assert not ok
 results[target]={'exit_code':c.returncode,'proof_success':ok}
out={'results':results,'cells':len(cells),'boundary_bits':len(leaves),'valid_register':vr,'privilege_register':pr,'reset_base':'Actual valid ARST255=0 makes valid=>priv11 vacuous regardless unreset privilege.','scope':'Binary exact combinational D induction under current valid=>priv11 and inactive reset; asynchronous asserted reset clears valid. Does not prove four-state event correspondence, native interrupt controls or full replay.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [src,D/'cut.json',D/'miter.v',D/'bad.log',D/'missing_base_bad.log',D/'inverted_privilege_bad.log']}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
