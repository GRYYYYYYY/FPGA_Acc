"""Actual original PC/valid next-state cones under current guarded relations."""
import json,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';mf=E/'full_original_unoptimized_proc_state_v1_2026-10-09/source_unoptimized.json';m=max(json.loads(mf.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})));inv=E/'full_original_pc_valid_capture_inventory_v1_2026-10-09/audit.json';a=json.loads(inv.read_text());D=E/'full_pc_valid_guard_step_v1_2026-10-09';D.mkdir(exist_ok=True)
# First test execute/memory/writeBack. IBus validity relationship requires its own frontend joins.
qs=[777,11168,11232,11286];vs=[m['netnames']['decode_arbitration_isValid']['bits'][0],8209,8216,8222];targets=[]
for q,v in zip(qs[1:],vs[1:]):
 qc=next(c for c in m['cells'].values() if q in c['connections'].get('Q',[]));vc=next(c for c in m['cells'].values() if v in c['connections'].get('Q',[]));targets.extend([qc['connections']['D'][qc['connections']['Q'].index(q)],vc['connections']['D'][vc['connections']['Q'].index(v)]])
drivers={b:(cn,c) for cn,c in m['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs if isinstance(b,int)};used={};leaves=set();seen=set()
def walk(b):
 if not isinstance(b,int) or b in seen:return
 seen.add(b)
 if b not in drivers:leaves.add(b);return
 cn,c=drivers[b]
 if 'dff' in c['type'].lower() or c['type'].startswith('$mem'):leaves.add(b);return
 used[cn]=c
 for p,bs in c['connections'].items():
  if c['port_directions'][p]=='input':
   for x in bs:walk(x)
for b in targets:walk(b)
leaves.update(qs+vs);leaves=sorted(leaves);index={b:i for i,b in enumerate(leaves)};ports={'roots':{'direction':'output','bits':targets},'boundary':{'direction':'input','bits':leaves}};(D/'cut.json').write_text(json.dumps({'modules':{'actual_cut':{'attributes':{},'ports':ports,'cells':used,'netnames':{}}}},indent=2)+'\n')
expr=lambda b:'boundary['+str(index[b])+']';guards=['(~'+expr(v)+' | ~'+expr(q)+')' for q,v in zip(qs,vs)];terms=['(roots['+str(2*i+1)+'] & roots['+str(2*i)+'])' for i in range(3)]
v='module miter(input ['+str(len(leaves)-1)+':0] boundary,output bad);wire [5:0] roots;actual_cut u(.boundary(boundary),.roots(roots));assign bad=('+' & '.join(guards)+') & ('+' | '.join(terms)+');endmodule\n';(D/'miter.v').write_text(v)
y=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';p=subprocess.run([str(y),'-p','read_json cut.json; read_verilog miter.v; prep -top miter; flatten; sat -prove bad 0 -show-inputs -show-outputs -show roots'],cwd=D,capture_output=True,text=True,timeout=60);log=p.stdout+p.stderr;(D/'check.log').write_text(log);assert p.returncode==0;success='SAT proof finished - no model found: SUCCESS!' in log;counterexample='SAT proof finished - model found: FAIL!' in log;assert success or counterexample
out={'success':success,'counterexample':counterexample,'exit_code':p.returncode,'cells':len(used),'leaves':len(leaves),'current_pc_bits':qs,'current_valid_bits':vs,'next_positions':['execute_pc0','execute_valid','memory_pc0','memory_valid','writeBack_pc0','writeBack_valid'],'boundary_bits':leaves,'scope':'Three actual original PC bit0/validD cones under four current valid-implies-PC0 premises, binary reset inactive. Other FF/memory/primary leaves arbitrary, no initial/global relation. Counterexample may identify missing boundary constraints, not actual reachable Full violation. Bit1 and frontend guard base remain unproved.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [mf,inv,D/'cut.json',D/'miter.v',D/'check.log']}};(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['hashes','boundary_bits']},indent=2))
