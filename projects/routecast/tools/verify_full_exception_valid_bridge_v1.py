import json,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';mf=E/'full_original_unoptimized_proc_state_v1_2026-10-09/source_unoptimized.json';m=max(json.loads(mf.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})));bit=lambda name:m['netnames'][name]['bits'][0]
wvalid=bit('writeBack_arbitration_isValid');mvalid=bit('memory_arbitration_isValid');wreg=bit('CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_writeBack');wexc=bit('CsrPlugin_exceptionPortCtrl_exceptionValids_writeBack');mexc=bit('CsrPlugin_exceptionPortCtrl_exceptionValids_memory')
def ff(q):return next(c for c in m['cells'].values() if q in c['connections'].get('Q',[]))
def data(q):c=ff(q);return c['connections']['D'][c['connections']['Q'].index(q)]
for q in [wreg,wvalid]:
 c=ff(q);assert c['type']=='$adff' and c['connections']['ARST']==[255] and c['parameters']['ARST_VALUE'][-1-c['connections']['Q'].index(q)]=='0'
roots=[wexc,data(wreg),data(wvalid),mexc];drivers={b:(name,c) for name,c in m['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs if isinstance(b,int)};used={};leaves=set();seen=set()
def walk(b):
 if not isinstance(b,int) or b in seen:return
 seen.add(b)
 if b not in drivers:leaves.add(b);return
 name,c=drivers[b]
 if 'dff' in c['type'].lower() or c['type'].startswith('$mem'):leaves.add(b);return
 if name in used:return
 used[name]=c
 for p,bs in c['connections'].items():
  if c['port_directions'][p]=='input':
   for x in bs:walk(x)
for b in roots:walk(b)
leaves.update([wvalid,mvalid,wreg]);leaves=sorted(leaves);idx={b:i for i,b in enumerate(leaves)};D=E/'full_exception_valid_bridge_v1_2026-10-09';D.mkdir(exist_ok=True);ports={'roots':{'direction':'output','bits':roots},'boundary':{'direction':'input','bits':leaves}};(D/'cut.json').write_text(json.dumps({'modules':{'actual_cut':{'attributes':{},'ports':ports,'cells':used,'netnames':{}}}},indent=2)+'\n');q=lambda b:'boundary['+str(idx[b])+']';v='module miter(input ['+str(len(leaves)-1)+':0] boundary,output comb_bad,step_bad);wire [3:0] roots;actual_cut u(.boundary(boundary),.roots(roots));wire premise=(~'+q(wreg)+' | '+q(wvalid)+');assign comb_bad=premise & roots[0] & ~'+q(wvalid)+';assign step_bad=premise & (~roots[3] | '+q(mvalid)+') & roots[1] & ~roots[2];endmodule\n';(D/'miter.v').write_text(v)
y=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';results={}
for target in ['comb_bad','step_bad']:
 p=subprocess.run([str(y),'-p',f'read_json cut.json; read_verilog miter.v; prep -top miter; flatten; sat -prove {target} 0 -show-inputs -show roots'],cwd=D,capture_output=True,text=True,timeout=60);log=p.stdout+p.stderr;(D/(target+'.log')).write_text(log);assert p.returncode==0;results[target]={'exit_code':p.returncode,'success':'SAT proof finished - no model found: SUCCESS!' in log,'counterexample':'SAT proof finished - model found: FAIL!' in log};assert results[target]['success'] or results[target]['counterexample']
out={'results':results,'cells':len(used),'leaves':len(leaves),'bits':{'writeBack_valid':wvalid,'memory_valid':mvalid,'writeBack_exception_register':wreg},'scope':'Actual WB exception combinational/registered next-state relation under current exception-register⇒WBvalid and, for step, memory exception⇒memoryvalid. Both actualWB registers reset0, but memory premise still needs base/preservation. No global inductive closure, PC bit1 or Full admission.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [mf,D/'cut.json',D/'miter.v',D/'comb_bad.log',D/'step_bad.log']}};(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['results','cells','leaves','scope']},indent=2))
