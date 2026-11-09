"""Compare complete actual unreset execute-instruction capture functions."""
import json,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_execute_instruction_capture_bridge_v1_2026-10-09';D.mkdir(exist_ok=True)
y=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys'
state_names=['execute_INSTRUCTION']
names=state_names+['decode_INSTRUCTION','execute_arbitration_isStuck']
rootnames=state_names
retained_lanes=[i for i in range(32) if i not in [0,1,2,3,4,6]]
records={};decl=[];ports=[];inst=[];pairs=[]
for label,rel in [('s','full_original_unoptimized_proc_state_v1_2026-10-09/source_unoptimized.json'),('n','full_native_ram_gates_v3_2026-10-09/gates.json')]:
 src=R/'experiments'/rel;m=max(json.loads(src.read_text())['modules'].values(),key=lambda m:len(m['cells']))
 bs=[m['netnames'][name]['bits'] for name in names];roots=[];reset_states=[]
 for lane in retained_lanes:
  q=bs[0][lane]
  matches=[(k,c) for k,c in m['cells'].items() if q in c['connections'].get('Q',[])];assert len(matches)==1
  k,c=matches[0];qlane=c['connections']['Q'].index(q)
  if label=='s':assert c['type']=='$dff' and c['connections']['CLK']==[254]
  else:assert c['type']=='$_DFF_P_' and c['connections']['C']==[254]
  assert not any('init' in v.get('attributes',{}) for v in m['netnames'].values() if q in v['bits'])
  roots.append(c['connections']['D'][qlane]);reset_states.append({'signal':'execute_INSTRUCTION','lane':lane,'cell':k,'register_lane':qlane,'definition':c})
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
 inst.append('wire [25:0] '+label+'r;'+label+'_cut u'+label+'(.boundary('+label+'),.roots('+label+'r));')
 expr=[]
 for bi,bits in enumerate(bs):
  if bi<2:bits=[bits[i] for i in retained_lanes]
  expr.append('{'+','.join(label+'['+str(index[b])+']' if isinstance(b,int) else "1'b"+b for b in reversed(bits))+'}')
 decl.append(expr);records[label]={'cells':len(cells),'boundary_bits':boundary,'named_boundary':dict(zip(names,bs)),'roots':{'retained_instruction_lanes':retained_lanes,'D_bits':roots},'reset_states':reset_states,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest()}
paired=' && '.join('('+a+' == '+b+')' for a,b in zip(*decl))
input_equal=' && '.join('('+a+' == '+b+')' for a,b in zip(decl[0][-2:],decl[1][-2:]))
capture='('+input_equal+') && !'+decl[0][-1]
v='module miter('+','.join(ports)+',output bad,capture_bad,missing_capture_bad,missing_boundary_bad);'+''.join(inst)+'assign missing_boundary_bad=|(sr ^ nr);assign bad=('+paired+') && missing_boundary_bad;assign capture_bad=('+capture+') && missing_boundary_bad;assign missing_capture_bad=('+input_equal+') && missing_boundary_bad;endmodule\n';(D/'miter.v').write_text(v)
checks={}
for target,expected in [('bad',True),('capture_bad',True),('missing_capture_bad',False),('missing_boundary_bad',False)]:
 cmd='read_json s_cut.json n_cut.json; read_verilog miter.v '+str(y.parents[1]/'share/yosys/simcells.v')+'; prep -top miter; flatten; sat -prove '+target+' 0 -show-inputs -show-outputs'
 c=subprocess.run([str(y),'-p',cmd],cwd=D,capture_output=True,text=True,timeout=30);log=c.stdout+c.stderr;(D/(target+'.log')).write_text(log)
 ok='SAT proof finished - no model found: SUCCESS!' in log;assert c.returncode==0 and ok==expected,(target,log[-1500:])
 checks[target]={'exit_code':c.returncode,'proof_success':ok}
out={'retained_lanes':retained_lanes,'excluded_native_alias_lanes':[0,1,2,3,4,6],'representations':records,'checks':checks,'scope':'All26 actual retained unreset execute instruction lanes hold while executeStuck, capture corresponding decode lanes otherwise; six undriven native aliases excluded with explicit inventory, not admitted. Paired D preservation under current-state/input equality and capture establishment with independent oldstates both proved. No reset/init invented; actual first unstuck capture, decoder data and consumer-valid history remain required','artifact_hashes':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [D/'s_cut.json',D/'n_cut.json',D/'miter.v',D/'bad.log',D/'missing_boundary_bad.log',D/'capture_bad.log',D/'missing_capture_bad.log']}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'checks':checks,'cells':{k:r['cells'] for k,r in records.items()},'scope':out['scope']},indent=2))
