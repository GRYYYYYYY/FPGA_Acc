"""Actual original/native mepc D versus software-write-first update expression."""
import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_mepc_update_priority_v1_2026-10-09';D.mkdir(exist_ok=True)
y=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys'
names={'old':'CsrPlugin_mepc','pc':'writeBack_PC','data':'CsrPlugin_csrMapping_writeDataSignal','sel':'execute_CsrPlugin_csr_833','we':'execute_CsrPlugin_writeEnable','trap':'when_CsrPlugin_l1310','debug':'when_CsrPlugin_l1318','priv':'CsrPlugin_targetPrivilege'}
results={}
for label,rel in [('source','full_original_unoptimized_proc_state_v1_2026-10-09/source_unoptimized.json'),('native','full_native_ram_gates_v3_2026-10-09/gates.json')]:
 src=R/'experiments'/rel;m=max(json.loads(src.read_text())['modules'].values(),key=lambda m:len(m['cells']))
 bs={k:m['netnames'][n]['bits'] for k,n in names.items()}
 drivers={b:(k,c) for k,c in m['cells'].items() for port,bits in c['connections'].items() if c['port_directions'][port]=='output' for b in bits if isinstance(b,int)}
 roots=[]
 for b in bs['old']:
  _,c=drivers[b];assert 'ff' in c['type'].lower();roots.append(c['connections']['D'][c['connections']['Q'].index(b)])
 boundary={b for bits in bs.values() for b in bits if isinstance(b,int)};cells={};leaves=set()
 def visit(b):
  if not isinstance(b,int):return
  if b in boundary:leaves.add(b);return
  assert b in drivers,(label,b)
  k,c=drivers[b];assert 'ff' not in c['type'].lower() and 'mem' not in c['type'].lower(),(label,k)
  if k in cells:return
  cells[k]=c
  for port,bits in c['connections'].items():
   if c['port_directions'][port]=='input':
    for x in bits:visit(x)
 for b in roots:visit(b)
 inputs=sorted(boundary);idx={b:i for i,b in enumerate(inputs)}
 ports={'boundary':{'direction':'input','bits':inputs},'next':{'direction':'output','bits':roots}}
 cut=D/(label+'_cut.json');cut.write_text(json.dumps({'modules':{'actual_cut':{'attributes':{},'ports':ports,'cells':cells,'netnames':{}}}},indent=2)+'\n')
 def expr(bits):return '{'+','.join('boundary['+str(idx[b])+']' if isinstance(b,int) else "1'b"+b for b in reversed(bits))+'}'
 decl=''.join('wire ['+str(len(bits)-1)+':0] '+k+'='+expr(bits)+';\n' for k,bits in bs.items())
 v='module miter(input ['+str(len(inputs)-1)+':0] boundary,output bad,wrong_priority_bad);wire [31:0] next;actual_cut u(.boundary(boundary),.next(next));'+decl+"wire trap_capture=trap && debug && priv==2'b11;wire [31:0] expected=(sel && we)?data:(trap_capture?pc:old);wire [31:0] wrong=trap_capture?pc:((sel && we)?data:old);assign bad=|(next ^ expected);assign wrong_priority_bad=|(next ^ wrong);endmodule\n"
 vf=D/(label+'_miter.v');vf.write_text(v);checks={}
 for target,expected in [('bad',True),('wrong_priority_bad',False)]:
  cmd=f'read_json {cut.name}; read_verilog {vf.name}; prep -top miter; flatten; sat -prove {target} 0 -show-inputs -show-outputs'
  if label=='native':cmd=f'read_json {cut.name}; read_verilog {vf.name}; read_verilog '+str(y.parents[1]/'share/yosys/simcells.v')+'; prep -top miter; flatten; sat -prove '+target+' 0 -show-inputs -show-outputs'
  c=subprocess.run([str(y),'-p',cmd],cwd=D,capture_output=True,text=True,timeout=30);log=c.stdout+c.stderr;(D/(label+'_'+target+'.log')).write_text(log)
  ok='SAT proof finished - no model found: SUCCESS!' in log
  assert c.returncode==0 and ok==expected,(label,target,c.returncode,log[-1500:])
  checks[target]={'exit_code':c.returncode,'proof_success':ok}
 results[label]={'cells':len(cells),'boundary_bits':len(inputs),'signal_bits':bs,'checks':checks,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest()}
out={'results':results,'scope':'Exact binary mepc update priority at named signal boundaries separately for source/native. Software CSR write wins over trap. Payload/control correspondence and initial mepc equality are not premises discharged by this check.'}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:{a:b for a,b in v.items() if a not in ['signal_bits','source_sha256']} for k,v in results.items()},indent=2))
