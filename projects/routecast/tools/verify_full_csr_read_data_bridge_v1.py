"""Compare actual complete CSR read-data logic at explicit selector/state boundaries."""
import json,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_csr_read_data_bridge_v1_2026-10-09';D.mkdir(exist_ok=True)
y=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys'
names=['execute_CsrPlugin_csr_768', 'execute_CsrPlugin_csr_256', 'execute_CsrPlugin_csr_384', 'execute_CsrPlugin_csr_836', 'execute_CsrPlugin_csr_772', 'execute_CsrPlugin_csr_833', 'execute_CsrPlugin_csr_834', 'execute_CsrPlugin_csr_835', 'MmuPlugin_status_mxr', 'MmuPlugin_status_sum', 'MmuPlugin_status_mprv', 'CsrPlugin_mstatus_MPIE', 'CsrPlugin_mstatus_MIE', 'CsrPlugin_mstatus_MPP', 'MmuPlugin_satp_mode', 'MmuPlugin_satp_asid', 'MmuPlugin_satp_ppn', 'CsrPlugin_mip_MEIP', 'CsrPlugin_mip_MTIP', 'CsrPlugin_mip_MSIP', 'CsrPlugin_mie_MEIE', 'CsrPlugin_mie_MTIE', 'CsrPlugin_mie_MSIE', 'CsrPlugin_mepc', 'CsrPlugin_mcause_interrupt', 'CsrPlugin_mcause_exceptionCode', 'CsrPlugin_mtval']
rootnames=['execute_CsrPlugin_readToWriteData']
records={};decl=[];ports=[];inst=[];pairs=[]
for label,rel in [('s','full_original_unoptimized_proc_state_v1_2026-10-09/source_unoptimized.json'),('n','full_native_ram_gates_v3_2026-10-09/gates.json')]:
 src=R/'experiments'/rel;m=max(json.loads(src.read_text())['modules'].values(),key=lambda m:len(m['cells']))
 bs=[m['netnames'][name]['bits'] for name in names];roots=sum([m['netnames'][name]['bits'] for name in rootnames],[])
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
v='module miter('+','.join(ports)+',output bad,missing_boundary_bad);'+''.join(inst)+'assign missing_boundary_bad=|(sr ^ nr);assign bad=('+paired+') && missing_boundary_bad;endmodule\n';(D/'miter.v').write_text(v)
checks={}
for target,expected in [('bad',True),('missing_boundary_bad',False)]:
 cmd='read_json s_cut.json n_cut.json; read_verilog miter.v '+str(y.parents[1]/'share/yosys/simcells.v')+'; prep -top miter; flatten; sat -prove '+target+' 0 -show-inputs -show-outputs'
 c=subprocess.run([str(y),'-p',cmd],cwd=D,capture_output=True,text=True,timeout=30);log=c.stdout+c.stderr;(D/(target+'.log')).write_text(log)
 ok='SAT proof finished - no model found: SUCCESS!' in log;assert c.returncode==0 and ok==expected,(target,log[-1500:])
 checks[target]={'exit_code':c.returncode,'proof_success':ok}
out={'representations':records,'checks':checks,'scope':'Actual complete32 CSR read-to-write data agrees under eight paired selection bits and actual CSR state boundary values. No one-hot assumption on selections. State reset/history equality, folded-state guards and four-state mux behavior remain open.','artifact_hashes':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [D/'s_cut.json',D/'n_cut.json',D/'miter.v',D/'bad.log',D/'missing_boundary_bad.log']}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'checks':checks,'cells':{k:r['cells'] for k,r in records.items()},'scope':out['scope']},indent=2))
