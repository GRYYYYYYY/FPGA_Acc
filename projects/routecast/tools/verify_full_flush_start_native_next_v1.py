import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';F=E/'full_native_ram_gates_v3_2026-10-09/gates.json';S=E/'full_source_export_fixed_bus_replay_v19_2026-10-09/reference.v';m=max(json.loads(F.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})));drivers={b:(n,c) for n,c in m['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs};names=['stageB_flusher_waitDone','stageB_flusher_start','io_cpu_flush_valid','io_cpu_execute_isValid','io_cpu_memory_isValid','io_cpu_writeBack_isValid','io_cpu_redo'];roots=[3120]+[m['netnames']['dataCache_1.'+n]['bits'][0] for n in names];used={};leaves=set()
def walk(b):
 if not isinstance(b,int):return
 entry=drivers.get(b)
 if entry is None or 'DFF' in entry[1]['type'] or entry[1]['type'].startswith('rc_'):leaves.add(b);return
 if b in used:return
 used[b]=entry
 for p,bs in entry[1]['connections'].items():
  if entry[1]['port_directions'][p]=='input':
   for x in bs:walk(x)
for b in roots:walk(b)
def sig(b):return 'n'+str(b) if isinstance(b,int) else "1'b"+b
lines=['module miter(input ['+str(len(leaves)-1)+':0] boundary,output equal);']
for i,b in enumerate(sorted(leaves)):lines.append('wire '+sig(b)+' = boundary['+str(i)+'];')
for b,(n,c) in used.items():
 co=c['connections'];a=sig(co['A'][0]);t=c['type']
 if t=='$_NOT_':expr='~'+a
 elif t in ['$_AND_','$_OR_']:expr=a+(' & ' if t=='$_AND_' else ' | ')+sig(co['B'][0])
 elif t=='$_MUX_':expr=sig(co['S'][0])+' ? '+sig(co['B'][0])+' : '+a
 else:raise ValueError(t)
 lines.append('wire '+sig(b)+' = '+expr+';')
w,start,flush,ex,mem,wb,redo=map(sig,roots[1:]);lines+=['wire expected = ~'+w+' & ~'+start+' & '+flush+' & ~'+ex+' & ~'+mem+' & ~'+wb+' & ~'+redo+';','assign equal = ('+sig(roots[0])+' == expected);','endmodule'];d=E/'full_flush_start_native_next_v1_2026-10-09';d.mkdir(exist_ok=True);(d/'miter.v').write_text('\n'.join(lines)+'\n');yosys=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';cmd=[str(yosys),'-p','read_verilog miter.v; prep -top miter; flatten; sat -verify -prove equal 1 -show-inputs'];r=subprocess.run(cmd,cwd=d,capture_output=True,text=True,timeout=60);(d/'check.log').write_text(r.stdout+r.stderr);assert r.returncode==0 and 'SAT proof finished - no model found: SUCCESS!' in r.stdout
cell=drivers[3121][1];assert cell['type']=='$_DFF_PP1_' and cell['connections']=={'C':[254],'D':[3120],'Q':[3121],'R':[255]}
assert 'stageB_flusher_start <= (((((((! stageB_flusher_waitDone)' in S.read_text()
out={'actual_cells':{n:c for n,c in used.values()},'boundary_bits':sorted(leaves),'semantic_roots':dict(zip(['native_D']+names,roots)),'proof_exit_code':r.returncode,'reset_clock_cell':cell,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [F,S,d/'miter.v',d/'check.log']},'scope':'Actual native combinational start-D equals original source Boolean expression under shared semantic roots,24 arbitrary underlying state leaves. Native reset1/clock/reset pins checked. Not full source/native root relation, reset event or global initialization proof.'};(d/'next_state_audit.json').write_text(json.dumps(out,indent=2)+'\n');print('SAT passed:47 actual native gates,24 arbitrary state leaves; start FF reset1 metadata matched')
