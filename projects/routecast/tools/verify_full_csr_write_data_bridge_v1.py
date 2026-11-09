"""Compare actual complete CSR write-data logic at explicit operand boundary."""
import json,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_csr_write_data_bridge_v1_2026-10-09';D.mkdir(exist_ok=True)
y=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys'
names=['execute_SRC1','execute_CsrPlugin_readToWriteData','execute_INSTRUCTION']
rootnames=['CsrPlugin_csrMapping_writeDataSignal']
records={};decl=[];ports=[];inst=[];pairs=[]
for label,rel in [('s','full_original_unoptimized_proc_state_v1_2026-10-09/source_unoptimized.json'),('n','full_native_ram_gates_v3_2026-10-09/gates.json')]:
 src=R/'experiments'/rel;m=max(json.loads(src.read_text())['modules'].values(),key=lambda m:len(m['cells']))
 bs=[m['netnames'][name]['bits'] for name in names];bs[-1]=bs[-1][12:14];roots=sum([m['netnames'][name]['bits'] for name in rootnames],[])
 boundary=sorted({b for bits in bs for b in bits if isinstance(b,int)});index={b:i for i,b in enumerate(boundary)}
 drivers={b:(k,c) for k,c in m['cells'].items() for port,bits in c['connections'].items() if c['port_directions'][port]=='output' for b in bits if isinstance(b,int)};cells={}
 def visit(b):
  if not isinstance(b,int) or b in index:return
  assert b in drivers,(label,b)
  k,c=drivers[b];assert 'ff' not in c['type'].lower() and 'mem' not in c['type'].lower(),(label,k)
  if k in cells:return
  cells[k]=c
  for port,bits in c['connections'].items():
   if c['port_directions'][port]=='input':
    for x in bits:visit(x)
 for b in roots:visit(b)
 cut=D/(label+'_cut.json');cut.write_text(json.dumps({'modules':{label+'_cut':{'attributes':{},'ports':{'boundary':{'direction':'input','bits':boundary},'roots':{'direction':'output','bits':roots}},'cells':cells,'netnames':{}}}},indent=2)+'\n')
 ports.append('input ['+str(len(boundary)-1)+':0] '+label)
 inst.append('wire [31:0] '+label+'r;'+label+'_cut u'+label+'(.boundary('+label+'),.roots('+label+'r));')
 expr=[]
 for bits in bs:
  expr.append('{'+','.join(label+'['+str(index[b])+']' if isinstance(b,int) else "1'b"+b for b in reversed(bits))+'}')
 decl.append(expr);records[label]={'cells':len(cells),'boundary_bits':boundary,'named_boundary':dict(zip(names,bs)),'roots':{name:m['netnames'][name]['bits'] for name in rootnames},'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest()}
paired=' && '.join('('+a+' == '+b+')' for a,b in zip(*decl))
qualified='('+decl[0][0]+' == '+decl[1][0]+') && ('+decl[0][2]+' == '+decl[1][2]+') && ((('+decl[0][2]+" & 2'b10)==0) || ("+decl[0][1]+' == '+decl[1][1]+'))'
v='module miter('+','.join(ports)+',output bad,qualified_read_bad,missing_boundary_bad);'+''.join(inst)+'assign missing_boundary_bad=|(sr ^ nr);assign qualified_read_bad=('+qualified+') && missing_boundary_bad;assign bad=('+paired+') && missing_boundary_bad;endmodule\n';(D/'miter.v').write_text(v)
checks={}
for target,expected in [('bad',True),('qualified_read_bad',True),('missing_boundary_bad',False)]:
 cmd='read_json s_cut.json n_cut.json; read_verilog miter.v '+str(y.parents[1]/'share/yosys/simcells.v')+'; prep -top miter; flatten; sat -prove '+target+' 0 -show-inputs -show-outputs'
 c=subprocess.run([str(y),'-p',cmd],cwd=D,capture_output=True,text=True,timeout=30);log=c.stdout+c.stderr;(D/(target+'.log')).write_text(log)
 ok='SAT proof finished - no model found: SUCCESS!' in log;assert c.returncode==0 and ok==expected,(target,log[-1500:])
 checks[target]={'exit_code':c.returncode,'proof_success':ok}
out={'representations':records,'checks':checks,'scope':'Actual full32 CSR write-data functions agree under paired SRC1, readToWriteData and instruction12/13. Read-data equality is needed only when instruction13=1; overwrite mode does not require it. Operand state/CSR read-data histories and four-state semantics remain open.','artifact_hashes':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [D/'s_cut.json',D/'n_cut.json',D/'miter.v',D/'bad.log',D/'missing_boundary_bad.log',D/'qualified_read_bad.log']}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'checks':checks,'cells':{k:r['cells'] for k,r in records.items()},'scope':out['scope']},indent=2))
