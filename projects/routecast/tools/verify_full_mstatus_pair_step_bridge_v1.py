"""Compare actual paired MIE/MPIE D under guarded trap-selection folding."""
import json,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_mstatus_pair_step_bridge_v1_2026-10-09';D.mkdir(exist_ok=True)
y=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys'
state_names=['CsrPlugin_mstatus_MIE','CsrPlugin_mstatus_MPIE']
names=state_names+['execute_CsrPlugin_csr_768','execute_CsrPlugin_writeEnable','CsrPlugin_csrMapping_writeDataSignal','when_CsrPlugin_l1310','when_CsrPlugin_l1376','switch_CsrPlugin_l1380','when_CsrPlugin_l1318','CsrPlugin_targetPrivilege']
rootnames=state_names
records={};decl=[];ports=[];inst=[];pairs=[]
for label,rel in [('s','full_original_unoptimized_proc_state_v1_2026-10-09/source_unoptimized.json'),('n','full_native_ram_gates_v3_2026-10-09/gates.json')]:
 src=R/'experiments'/rel;m=max(json.loads(src.read_text())['modules'].values(),key=lambda m:len(m['cells']))
 bs=[m['netnames'][name]['bits'] for name in names];bs[4]=[bs[4][i] for i in [3,7]];roots=[];reset_states=[]
 for name in state_names:
  q=m['netnames'][name]['bits'];assert len(q)==1
  matches=[(k,c) for k,c in m['cells'].items() if c['connections'].get('Q')==q];assert len(matches)==1
  k,c=matches[0]
  if label=='s':assert c['type']=='$adff' and c['parameters']['ARST_VALUE']=='0' and c['parameters']['ARST_POLARITY']=='1' and c['connections']['ARST']==[255] and c['connections']['CLK']==[254]
  else:assert c['type']=='$_DFF_PP0_' and c['connections']['R']==[255] and c['connections']['C']==[254]
  roots+=c['connections']['D'];reset_states.append({'signal':name,'cell':k,'definition':c})
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
 inst.append('wire [1:0] '+label+'r;'+label+'_cut u'+label+'(.boundary('+label+'),.roots('+label+'r));')
 expr=[]
 for bits in bs:
  expr.append('{'+','.join(label+'['+str(index[b])+']' if isinstance(b,int) else "1'b"+b for b in reversed(bits))+'}')
 decl.append(expr);records[label]={'cells':len(cells),'boundary_bits':boundary,'named_boundary':dict(zip(names,bs)),'roots':dict(zip(rootnames,roots)),'reset_states':reset_states,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest()}
paired=' && '.join('('+a+' == '+b+')' for a,b in zip(decl[0][:-2],decl[1][:-2]))
guard='(!'+decl[0][5]+' || ('+decl[0][8]+" && "+decl[0][9]+"==2'b11))"
v='module miter('+','.join(ports)+',output bad,missing_boundary_bad,missing_guard_bad);'+''.join(inst)+'assign missing_boundary_bad=|(sr ^ nr);assign missing_guard_bad=('+paired+') && missing_boundary_bad;assign bad=('+guard+') && missing_guard_bad;endmodule\n';(D/'miter.v').write_text(v)
checks={}
for target,expected in [('bad',True),('missing_boundary_bad',False),('missing_guard_bad',False)]:
 cmd='read_json s_cut.json n_cut.json; read_verilog miter.v '+str(y.parents[1]/'share/yosys/simcells.v')+'; prep -top miter; flatten; sat -prove '+target+' 0 -show-inputs -show-outputs'
 c=subprocess.run([str(y),'-p',cmd],cwd=D,capture_output=True,text=True,timeout=30);log=c.stdout+c.stderr;(D/(target+'.log')).write_text(log)
 ok='SAT proof finished - no model found: SUCCESS!' in log;assert c.returncode==0 and ok==expected,(target,log[-1500:])
 checks[target]={'exit_code':c.returncode,'proof_success':ok}
guardfile=R/'experiments/full_trap_privilege_selection_v1_2026-10-09/audit.json';ga=json.loads(guardfile.read_text());assert ga['results']['bad']['proof_success'];assert ga['hashes']['experiments/full_original_unoptimized_proc_state_v1_2026-10-09/source_unoptimized.json']==records['s']['source_sha256']
out={'guard_dependency':{'path':str(guardfile.relative_to(R)),'sha256':hashlib.sha256(guardfile.read_bytes()).hexdigest()},'representations':records,'checks':checks,'scope':'Actual paired MIE/MPIE reset bases and joint D equality under paired current states, CSRselect/writeEnable/data3/7, trapouter and return controls, plus source trapouter=>debugguard&&targetPrivilege11 (previously proved with capture guard). Does not assume unconditional privilege equality or prove upstream boundary histories/four-state correspondence','artifact_hashes':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [D/'s_cut.json',D/'n_cut.json',D/'miter.v',D/'bad.log',D/'missing_boundary_bad.log',D/'missing_guard_bad.log']}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'checks':checks,'cells':{k:r['cells'] for k,r in records.items()},'scope':out['scope']},indent=2))
