import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';files=[E/'full_ram_mapping_candidate_v1_2026-10-09/structural.json',E/'full_native_ram_gates_v3_2026-10-09/gates.json',E/'full_structural_native_register_mapping_v1_2026-10-09/mapping_audit.json'];s,n=[max(json.loads(f.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{}))) for f in files[:2]];mapping={r['bit']:r['native_candidates'][0] for r in json.loads(files[2].read_text())['rows'] if r['status'] in ['unique_native_state','constant']};dependency=json.loads((E/'full_datacache_control_step_dependencies_v1_2026-10-09/dependency_audit.json').read_text());base={'records':[{'intermediate_bit':r['intermediate_bits'][0],'native_bit':r['native_bit']} for r in dependency['records'] if r['kind']=='paired_register']};assert len(base['records'])==49;positions=[];transition_metadata=[];fresh=2000000

def mux(a,b,control,positive):
 global fresh
 fresh+=1;y=fresh;s['cells']['actual_update_mux_'+str(y)]={'hide_name':1,'type':'$mux','parameters':{'WIDTH':'1'},'attributes':{},'port_directions':{'A':'input','B':'input','S':'input','Y':'output'},'connections':{'A':[a if positive else b],'B':[b if positive else a],'S':[control],'Y':[y]}};return y
for i,r in enumerate(base['records']):
 q=r['intermediate_bit'];nq=r['native_bit'];sc=next(c for c in s['cells'].values() if q in c['connections'].get('Q',[]));nc=next(c for c in n['cells'].values() if c['connections'].get('Q')==[nq]);lane=sc['connections']['Q'].index(q);assert sc['type'] in ['$dff','$adff','$adffe','$dffe','$sdff','$sdffe','$sdffce'];assert sc['connections']['CLK']==nc['connections']['C']==[254];d=sc['connections']['D'][lane]
 def clear(value):return mux(value,sc['parameters']['SRST_VALUE'][-1-lane],sc['connections']['SRST'][0],int(sc['parameters']['SRST_POLARITY'],2))
 if sc['type']=='$sdffce':d=clear(d)
 if 'EN' in sc['connections']:d=mux(q,d,sc['connections']['EN'][0],int(sc['parameters']['EN_POLARITY'],2))
 if 'SRST' in sc['connections'] and sc['type']!='$sdffce':d=clear(d)
 positions.append({'name':'next_'+str(nq),'structural':d,'native':nc['connections']['D'][0]});transition_metadata.append({'structural_Q':q,'native_Q':nq,'structural_cell':sc,'native_cell':nc})

mods={};leafmaps={};coverage={};constants={};macro_pairs=[]
for cn,c in s['cells'].items():
 if c['type']=='dual_port_ram':
  other=n['cells'][cn];assert other['type']==c['type'] and other['parameters']==c['parameters']
  for port,bs in c['connections'].items():
   if c['port_directions'][port]=='output':
    otherbits=other['connections'][port];assert len(bs)==len(otherbits);mapping.update(zip(bs,otherbits));macro_pairs.append({'macro':cn,'port':port,'structural_bits':bs,'native_bits':otherbits})
for port,info in s['ports'].items():
 if info['direction']=='input':
  other=n['ports'][port];assert other['direction']=='input' and len(info['bits'])==len(other['bits']);mapping.update(zip(info['bits'],other['bits']))
for label,mod in [('structural',s),('native',n)]:
 primary={b for p in mod['ports'].values() if p['direction']=='input' for b in p['bits']}
 drivers={b:(cn,c) for cn,c in mod['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs};roots=[r[label] for r in positions];used={};leaves=set()
 def walk(b):
  if not isinstance(b,int):return
  if b in primary:leaves.add(b);return
  assert b in drivers,(label,b)
  cn,c=drivers[b]
  if 'dff' in c['type'].lower() or c['type']=='dual_port_ram':leaves.add(b);return
  assert not c['type'].startswith('$mem') and c['type']!='dual_port_ram',(label,'uncut memory',cn)
  if cn in used:return
  used[cn]=c
  for p,bs in c['connections'].items():
   if c['port_directions'][p]=='input':
    for x in bs:walk(x)
 for b in roots:walk(b)
 lm={b:(mapping.get(b,4000000+b) if isinstance(mapping.get(b,4000000+b),int) else 5000000+b) if label=='structural' else b for b in leaves};leafmaps[label]=lm
 for b,t in lm.items():
  if isinstance(t,str):constants[b]=t
 ports={'roots':{'direction':'output','bits':roots}}|{'i'+str(b):{'direction':'input','bits':[b]} for b in leaves};mods[label]={'attributes':{},'ports':ports,'cells':used,'netnames':{}};coverage[label]={'cells':len(used),'leaves':len(leaves)}
symbols=sorted({b for lm in leafmaps.values() for b in lm.values() if isinstance(b,int)});index={b:i for i,b in enumerate(symbols)};lines=['module miter(input ['+str(len(symbols)-1)+':0] shared,output bad);']
for label in mods:
 lines.append('wire [48:0] '+label+'_roots;');connections=['.roots('+label+'_roots)']
 for b,t in leafmaps[label].items():connections.append('.i'+str(b)+'('+('shared['+str(index[t])+']' if isinstance(t,int) else "1'b"+t)+')')
 lines.append(label+' u_'+label+'('+','.join(connections)+');')
lines+=['assign bad=|(structural_roots^native_roots);','endmodule'];D=E/'full_structural_native_datacache_dependency_steps_v2_2026-10-09';D.mkdir(exist_ok=True);(D/'cuts.json').write_text(json.dumps({'modules':mods},indent=2)+'\n');(D/'miter.v').write_text('\n'.join(lines)+'\n');yosys=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';cmd=[str(yosys),'-p','read_json cuts.json; read_verilog miter.v; prep -top miter; flatten; sat -verify -prove bad 0 -show-inputs'];r=subprocess.run(cmd,cwd=D,capture_output=True,text=True,timeout=60);(D/'check.log').write_text(r.stdout+r.stderr);out={'optimized_constant_state_independent_leaves':[b for b in leafmaps['structural'] if isinstance(mapping.get(b),str)],'unpaired_structural_independent_leaves':[b for b in leafmaps['structural'] if b not in mapping],'shared_macro_output_premises':macro_pairs,'transition_metadata':transition_metadata,'positions':positions,'coverage':coverage,'leafmaps':leafmaps,'constant_premises':constants,'shared_symbols':symbols,'exit_code':r.returncode,'success':'SAT proof finished - no model found: SUCCESS!' in r.stdout,'hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [*files,D/'cuts.json',D/'miter.v',D/'check.log']},'scope':'Actual structural/native 49 effective next-state functions, reset inactive under explicit named paired current FF equality, merged aliases if any and recorded constant premises. Actual macro output equality is an explicit oracle premise, not established arrays/addresses. No init/preservation of those state relations, original four-state equivalence or Full admission.'};(D/'condition_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['leafmaps','hashes','transition_metadata','shared_macro_output_premises']},indent=2));assert r.returncode==0 and out['success']
