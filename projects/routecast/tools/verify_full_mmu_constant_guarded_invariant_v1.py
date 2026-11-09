import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';F=E/'full_ram_mapping_candidate_v1_2026-10-09/structural.json';m=max(json.loads(F.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})));drivers={b:(n,c) for n,c in m['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs};state=[2344,2345,2346];port=3239;ff=drivers[state[0]][1];pf=drivers[port][1];assert ff['connections']['ARST']==[255] and ff['parameters']['ARST_VALUE']=='000';consumers=[(n,c) for n,c in m['cells'].items() if any(port in bs for p,bs in c['connections'].items() if c['port_directions'][p]=='input')];assert len(consumers)==1
assert all(port not in p['bits'] for p in m['ports'].values() if p['direction']=='output')
outputs={'state_d':ff['connections']['D'],'state_en':ff['connections']['EN'],'capture':pf['connections']['EN'],'capture_d':[pf['connections']['D'][0]],'busy':[7010]};used={};leaves=set();missing=set()
def walk(b):
 if not isinstance(b,int):return
 entry=drivers.get(b)
 if entry is None or 'dff' in entry[1]['type'].lower() or entry[1]['type'].startswith('rc_'):
  leaves.add(b);return
 n,c=entry
 if n in used:return
 used[n]=c
 for p,bs in c['connections'].items():
  if c['port_directions'][p]=='input':
   for x in bs:walk(x)
for bs in outputs.values():
 for b in bs:walk(b)
leaves.update(state+[port]);ordered=sorted(leaves);ports={'boundary':{'direction':'input','bits':ordered}}|{n:{'direction':'output','bits':bs} for n,bs in outputs.items()};d=E/'full_mmu_constant_guarded_invariant_v1_2026-10-09';d.mkdir(exist_ok=True);(d/'cone.json').write_text(json.dumps({'modules':{'cone':{'attributes':{},'ports':ports,'cells':used,'netnames':{}}}},indent=2)+'\n');state_expr='{'+','.join('boundary['+str(ordered.index(b))+']' for b in reversed(state))+'}';p='boundary['+str(ordered.index(port))+']';v='''module miter(input [%d:0] boundary,output good);
wire [2:0] state_d; wire state_en,capture,capture_d,busy;
cone c(.boundary(boundary),.state_d(state_d),.state_en(state_en),.capture(capture),.capture_d(capture_d),.busy(busy));
wire [2:0] oldstate=%s;
wire oldport=%s;
wire [2:0] nextstate=state_en?state_d:oldstate;
wire nextport=capture?capture_d:oldport;
wire invariant=(oldstate==0)||!oldport;
assign good=(!invariant)||(((nextstate==0)||!nextport)&&!busy);
endmodule
'''%(len(ordered)-1,state_expr,p);(d/'miter.v').write_text(v);yosys=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';cmd=[str(yosys),'-p','read_json cone.json; read_verilog miter.v; prep -top miter; flatten; sat -verify -prove good 1 -show-inputs'];r=subprocess.run(cmd,cwd=d,capture_output=True,text=True,timeout=60);(d/'negative.v').write_text(v.replace('capture?capture_d:oldport','oldport'));negative_cmd=[str(yosys),'-p','read_json cone.json; read_verilog negative.v; prep -top miter; flatten; sat -verify -prove good 1 -show-inputs'];negative=subprocess.run(negative_cmd,cwd=d,capture_output=True,text=True,timeout=60);(d/'negative.log').write_text(negative.stdout+negative.stderr);assert negative.returncode!=0 and 'proof did fail' in (negative.stdout+negative.stderr);(d/'check.log').write_text(r.stdout+r.stderr);out={'negative_capture_disabled_exit_code':negative.returncode,'cells':len(used),'boundary_bits':ordered,'consumers':dict(consumers),'proof_exit_code':r.returncode,'proof_success':'SAT proof finished - no model found: SUCCESS!' in r.stdout,'reset_base':'Actual state FF async reset0 establishes state==IDLE while port value may remain arbitrary. Binary reset-event premise required.','scope':'Exact intermediate actual cells for one-step inductive invariant state==IDLE OR portSortedOh0==0 and complete direct consumer busy masked under invariant. Not source/native FSM correspondence, X/Z event relation, global memory/state equivalence or Full admission.','hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [F,d/'cone.json',d/'miter.v',d/'check.log',d/'negative.v',d/'negative.log']}};(d/'invariant_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['consumers','hashes','boundary_bits']},indent=2));assert r.returncode==0 and out['proof_success']
