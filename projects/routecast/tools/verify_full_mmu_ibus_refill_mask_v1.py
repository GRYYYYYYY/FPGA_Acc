"""Actual MMU idle preservation under refill-request zero."""
import json,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_mmu_ibus_refill_mask_v1_2026-10-09';D.mkdir(exist_ok=True);y=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';results={}
for label,rel in [('s','full_original_unoptimized_proc_state_v1_2026-10-09/source_unoptimized.json')]:
 f=R/'experiments'/rel;m=max(json.loads(f.read_text())['modules'].values(),key=lambda m:len(m['cells']));q=m['netnames']['MmuPlugin_satp_mode']['bits'];roots=m['netnames']['MmuPlugin_ports_0_requireMmuLockupCalc']['bits']+[m['netnames']['MmuPlugin_shared_refills']['bits'][0]];regs=[];valid=q[0]
 drivers={b:(k,c) for k,c in m['cells'].items() for port,bs in c['connections'].items() if c['port_directions'][port]=='output' for b in bs if isinstance(b,int)};cells={};leaves=set(q+[valid])
 def visit(b):
  if not isinstance(b,int) or b in leaves:return
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
 qe='boundary['+str(ix[q[0]])+']';vf=D/(label+'_miter.v');vf.write_text('module miter(input ['+str(len(bits)-1)+':0] boundary,output bad,missing_mode_guard_bad);wire [1:0] roots;actual_cut u(.boundary(boundary),.roots(roots));assign bad=!'+qe+' && |roots;assign missing_mode_guard_bad=|roots;endmodule\n')
 checks={}
 for target,expected in [('bad',True),('missing_mode_guard_bad',True)]:
  cmd=f'read_json {cut.name}; read_verilog {vf.name} '+str(y.parents[1]/'share/yosys/simcells.v')+'; prep -top miter; flatten; sat -prove '+target+' 0 -show-inputs -show-outputs';p=subprocess.run([str(y),'-p',cmd],cwd=D,capture_output=True,text=True,timeout=30);log=p.stdout+p.stderr;(D/(label+'_'+target+'.log')).write_text(log);ok='SAT proof finished - no model found: SUCCESS!' in log;assert p.returncode==0 and ok==expected;checks[target]={'proof_success':ok,'exit_code':p.returncode}
 results[label]={'checks':checks,'cells':len(cells),'leaves':len(bits),'registers':regs,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
out={'artifact_hashes':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in D.iterdir() if f.suffix in ['.json','.v','.log'] and f.name!='audit.json'},'results':results,'scope':'Actual source fixed privilege11 forces IBus lookup requirement and priority-selected IBus refill bit0 unconditionally, independent of satp, MPP and DBus request. Binary combinational proof only; selection-register history remains separate.'};(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:{x:v for x,v in r.items() if x in ['checks','cells','leaves']} for k,r in results.items()},indent=2))
