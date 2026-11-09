import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';F=E/'full_original_source_proc_state_v1_2026-10-09/source_proc.json';m=max(json.loads(F.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})));drivers={b:(n,c,i) for n,c in m['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for i,b in enumerate(bs)};pairs=[(2014,2727),(2029,2720),(2025,2656),(2026,2688)];valid=[m['netnames'][n]['bits'][0] for n in ['execute_arbitration_isValid','memory_arbitration_isValid','writeBack_arbitration_isValid']];bits=sorted({b for p in pairs for b in p}|set(valid));outputs={};ffrecords={}
for b in bits:
 n,c,lane=drivers[b];assert c['type'] in ['$dffe','$adffe'];ffrecords[b]={'name':n,'cell':c,'lane':lane};outputs['d'+str(b)]=[c['connections']['D'][lane]];outputs['en'+str(b)]=c['connections']['EN']
for b in valid:
 c=ffrecords[b]['cell'];lane=ffrecords[b]['lane'];assert c['type']=='$adffe' and c['connections']['ARST']==[255] and int(c['parameters']['ARST_POLARITY'],2)==1 and c['parameters']['ARST_VALUE'][-1-lane]=='0'
assert all(r['cell']['connections']['CLK']==[254] and int(r['cell']['parameters']['CLK_POLARITY'],2)==1 for r in ffrecords.values())
used={};leaves=set(bits)
def walk(b):
 if not isinstance(b,int):return
 item=drivers.get(b)
 if item is None or 'dff' in item[1]['type'].lower() or item[1]['type'].startswith('$memrd'):leaves.add(b);return
 n,c,l=item
 if n in used:return
 used[n]=c
 for p,bs in c['connections'].items():
  if c['port_directions'][p]=='input':
   for x in bs:walk(x)
for bs in outputs.values():
 for b in bs:walk(b)
ordered=sorted(leaves);ports={'boundary':{'direction':'input','bits':ordered}}|{n:{'direction':'output','bits':bs} for n,bs in outputs.items()};D=E/'full_source_merged_valid_relation_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'cone.json').write_text(json.dumps({'modules':{'cone':{'attributes':{},'ports':ports,'cells':used,'netnames':{}}}},indent=2)+'\n');v=['module miter(input ['+str(len(ordered)-1)+':0] boundary, output good);']
for b in bits:
 c=ffrecords[b]['cell'];pol=int(c['parameters']['EN_POLARITY'],2);v+=['wire d'+str(b)+',en'+str(b)+';','wire old'+str(b)+'=boundary['+str(ordered.index(b))+'];','wire next'+str(b)+' = '+('' if pol else '~')+'en'+str(b)+' ? d'+str(b)+' : old'+str(b)+';']
v.append('cone c(.boundary(boundary),'+','.join('.'+n+'('+n+')' for n in outputs)+');')
def invariant(prefix):
 return ' & '.join('(!'+prefix+str(valid[stage])+' || ('+prefix+str(a)+' == '+prefix+str(b)+'))' for (a,b),stage in zip(pairs,[0,0,1,2]))
v+=['wire current_relation='+invariant('old')+';','wire next_relation='+invariant('next')+';','assign good= !current_relation || next_relation;','endmodule'];(D/'miter.v').write_text('\n'.join(v)+'\n');yosys=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';r=subprocess.run([str(yosys),'-p','read_json cone.json; read_verilog miter.v; prep -top miter; flatten; sat -verify -prove good 1 -show-inputs'],cwd=D,capture_output=True,text=True,timeout=60);(D/'check.log').write_text(r.stdout+r.stderr);out={'pairs':pairs,'stage_valid_bits':valid,'cells':len(used),'boundary_bits':ordered,'ff_metadata':ffrecords,'exit_code':r.returncode,'success':'SAT proof finished - no model found: SUCCESS!' in r.stdout,'scope':'Original-source exact binary one-step preservation of stage-valid implies merged-pair equality. Reset base requires actual stage-valid reset0 metadata. Not unconditional pair equality, all-consumer masking, native-state correspondence or Full admission.','hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [F,D/'cone.json',D/'miter.v',D/'check.log']}};(D/'relation_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['boundary_bits','ff_metadata','hashes']},indent=2));assert r.returncode==0 and out['success']
