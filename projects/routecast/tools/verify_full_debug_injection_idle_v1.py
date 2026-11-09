"""Actual reset-established debug idle preservation when shared cmd_valid=0."""
import json,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_debug_injection_idle_v1_2026-10-09';D.mkdir(exist_ok=True);y=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';results={}
for label,rel in [('s','full_original_unoptimized_proc_state_v1_2026-10-09/source_unoptimized.json'),('n','full_native_ram_gates_v3_2026-10-09/gates.json')]:
 f=R/'experiments'/rel;m=max(json.loads(f.read_text())['modules'].values(),key=lambda m:len(m['cells']));q=m['netnames']['switch_Fetcher_l365']['bits'];roots=[];regs=[]
 for bit in q:
  c=next(c for c in m['cells'].values() if bit in c['connections'].get('Q',[]));lane=c['connections']['Q'].index(bit)
  if label=='s':assert c['type']=='$adff' and c['parameters']['ARST_VALUE']=='000' and c['connections']['ARST']==[255]
  else:assert c['type']=='$_DFF_PP0_' and c['connections']['R']==[255]
  roots.append(c['connections']['D'][lane]);regs.append(c)
 roots+=m['netnames']['IBusCachedPlugin_cache.when_Fetcher_l401']['bits']+m['netnames']['IBusCachedPlugin_injectionPort_valid']['bits'];valid=m['ports']['debug_bus_cmd_valid']['bits'][0]
 drivers={b:(k,c) for k,c in m['cells'].items() for port,bs in c['connections'].items() if c['port_directions'][port]=='output' for b in bs if isinstance(b,int)};cells={};leaves=set(q+[valid])
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
 bits=sorted(leaves);ix={b:i for i,b in enumerate(bits)};cut=D/(label+'_cut.json');cut.write_text(json.dumps({'modules':{'actual_cut':{'attributes':{},'ports':{'boundary':{'direction':'input','bits':bits},'roots':{'direction':'output','bits':roots}},'cells':cells,'netnames':{}}}},indent=2)+'\n')
 qe='{'+','.join('boundary['+str(ix[b])+']' for b in reversed(q))+'}';ve='boundary['+str(ix[valid])+']';vf=D/(label+'_miter.v');vf.write_text('module miter(input ['+str(len(bits)-1)+':0] boundary,output bad,missing_reset_bad,missing_command_guard_bad);wire [4:0] roots;actual_cut u(.boundary(boundary),.roots(roots));assign bad=('+qe+"==3'b000) && !"+ve+' && |roots;assign missing_reset_bad=!'+ve+' && |roots;assign missing_command_guard_bad=('+qe+"==3'b000) && |roots;endmodule\n")
 checks={}
 for target,expected in [('bad',True),('missing_reset_bad',False),('missing_command_guard_bad',False)]:
  cmd=f'read_json {cut.name}; read_verilog {vf.name} '+str(y.parents[1]/'share/yosys/simcells.v')+'; prep -top miter; flatten; sat -prove '+target+' 0 -show-inputs -show-outputs';p=subprocess.run([str(y),'-p',cmd],cwd=D,capture_output=True,text=True,timeout=30);log=p.stdout+p.stderr;(D/(label+'_'+target+'.log')).write_text(log);ok='SAT proof finished - no model found: SUCCESS!' in log;assert p.returncode==0 and ok==expected;checks[target]={'proof_success':ok,'exit_code':p.returncode}
 results[label]={'checks':checks,'cells':len(cells),'leaves':len(bits),'registers':regs,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
out={'results':results,'scope':'Actual binary reset-base/idle preservation with debugcmdValid0, and injection/override outputs0. Frozen tb cmdValid binding and four-state/event scope separate.'};(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:{x:v for x,v in r.items() if x in ['checks','cells','leaves']} for k,r in results.items()},indent=2))
