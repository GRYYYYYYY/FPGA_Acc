import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';files=[E/'full_ram_mapping_candidate_v1_2026-10-09/structural.json',E/'full_native_ram_gates_v3_2026-10-09/gates.json',E/'full_structural_native_register_mapping_v1_2026-10-09/mapping_audit.json'];s,n=[max(json.loads(f.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{}))) for f in files[:2]];mapping={r['bit']:r['native_candidates'][0] for r in json.loads(files[2].read_text())['rows'] if r['status'] in ['unique_native_state','constant']};positions=[]
padding_audit=E/'full_datacache_tag_pending_padding_v1_2026-10-09/audit.json'
padding=json.loads(padding_audit.read_text());assert padding['source_sha256']==hashlib.sha256(files[0].read_bytes()).hexdigest()
assert all(padding['results'][k]['success'] for k in ['base_bad','step_bad'])
padding_bits={b for row in padding['rows'] for b in row['pa_connections']['Q'][7:]}
assert len(padding_bits)==6
for b in padding_bits:
 assert mapping[b]=='0'
 mapping[b]=100000+b
files.append(padding_audit)
for slice_index in [0,1]:
 cn='dataCache_1.ways_0_tags.s'+str(slice_index)+'.ram';sc=s['cells'][cn];nc=n['cells'][cn];assert sc['type']==nc['type']=='dual_port_ram' and sc['parameters']==nc['parameters']
 for port,old in sc['connections'].items():
  if sc['port_directions'][port]!='input':continue
  other=nc['connections'][port];assert len(old)==len(other)
  for lane,(x,y) in enumerate(zip(old,other)):
   if port.startswith('data') and slice_index==1 and lane>=2:continue
   positions.append({'name':cn+'.'+port+'['+str(lane)+']','structural':x,'native':y})
positions.append({'name':'logical_tag_read_valid','structural':s['netnames']['dataCache_1.tagsReadCmd_valid']['bits'][0],'native':n['netnames']['dataCache_1.tagsReadCmd_valid']['bits'][0]})
capture_metadata=[]
for i in [0,1]:
 prefix='dataCache_1.ways_0_tags.s'+str(i)
 for suffix in ['er','hit']:
  qs=s['netnames'][prefix+'.'+suffix]['bits'];qn=n['netnames'][prefix+'.'+suffix]['bits']
  sc=next(c for c in s['cells'].values() if c['connections'].get('Q')==qs)
  nc=next(c for c in n['cells'].values() if c['connections'].get('Q')==qn)
  assert sc['type']=='$dff' and nc['type']=='$_DFF_P_'
  assert sc['connections']['CLK']==nc['connections']['C']==[254]
  positions.append({'name':prefix+'.next_'+suffix,'structural':sc['connections']['D'][0],'native':nc['connections']['D'][0]})
  capture_metadata.append({'name':prefix+'.'+suffix,'structural_cell':sc,'native_cell':nc})
mods={};leafmaps={};coverage={};constants={}
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
  if 'dff' in c['type'].lower():leaves.add(b);return
  assert not c['type'].startswith('$mem') and c['type']!='dual_port_ram',(label,'uncut memory',cn)
  if cn in used:return
  used[cn]=c
  for p,bs in c['connections'].items():
   if c['port_directions'][p]=='input':
    for x in bs:walk(x)
 for b in roots:walk(b)
 lm={b:mapping[b] if label=='structural' else b for b in leaves};leafmaps[label]=lm
 for b,t in lm.items():
  if isinstance(t,str):constants[b]=t
 ports={'roots':{'direction':'output','bits':roots}}|{'i'+str(b):{'direction':'input','bits':[b]} for b in leaves};mods[label]={'attributes':{},'ports':ports,'cells':used,'netnames':{}};coverage[label]={'cells':len(used),'leaves':len(leaves)}
symbols=sorted({b for lm in leafmaps.values() for b in lm.values() if isinstance(b,int)});index={b:i for i,b in enumerate(symbols)};lines=['module miter(input ['+str(len(symbols)-1)+':0] shared,output bad);']
for label in mods:
 lines.append('wire ['+str(len(positions)-1)+':0] '+label+'_roots;');connections=['.roots('+label+'_roots)']
 for b,t in leafmaps[label].items():connections.append('.i'+str(b)+'('+('shared['+str(index[t])+']' if isinstance(t,int) else "1'b"+t)+')')
 lines.append(label+' u_'+label+'('+','.join(connections)+');')
read_index=next(i for i,p in enumerate(positions) if p['name']=='logical_tag_read_valid');terms=[];guards=[]
for row in padding['rows']:
 prefix=row['slice']+'.ram'
 wi=next(i for i,p in enumerate(positions) if p['name']==prefix+'.we1[0]')
 high=[next(i for i,p in enumerate(positions) if p['name']==prefix+'.addr1['+str(lane)+']') for lane in [7,8,9]]
 guards.append('(~structural_roots['+str(wi)+'] | ~('+' | '.join('structural_roots['+str(j)+']' for j in high)+'))')
for i,p in enumerate(positions):
 term='(structural_roots['+str(i)+'] ^ native_roots['+str(i)+'])'
 if '.addr2[' in p['name']:term='(structural_roots['+str(read_index)+'] & '+term+')'
 if '.addr1[' in p['name'] or '.data1[' in p['name']:
  prefix=p['name'].split('.ram.')[0]+'.ram'
  wi=next(j for j,q in enumerate(positions) if q['name']==prefix+'.we1[0]')
  term='(structural_roots['+str(wi)+'] & '+term+')'
 if p['name'].endswith('.next_hit'):
  ri=next(j for j,q in enumerate(positions) if q['name']==p['name'].replace('.next_hit','.next_er'))
  term='(structural_roots['+str(ri)+'] & '+term+')'
 terms.append(term)
lines+=['wire invariant_ok='+' & '.join(guards)+';','assign bad=invariant_ok & ('+' | '.join(terms)+');','endmodule'];D=E/'full_structural_native_datacache_tag_capture_bridge_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'cuts.json').write_text(json.dumps({'modules':mods},indent=2)+'\n');(D/'miter.v').write_text('\n'.join(lines)+'\n');yosys=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';cmd=[str(yosys),'-p','read_json cuts.json; read_verilog miter.v; prep -top miter; flatten; sat -verify -prove bad 0 -show-inputs'];r=subprocess.run(cmd,cwd=D,capture_output=True,text=True,timeout=60);(D/'check.log').write_text(r.stdout+r.stderr);out={'capture_metadata':capture_metadata,'positions':positions,'coverage':coverage,'leafmaps':leafmaps,'guarded_padding_premises':padding['invariant'],'independent_padding_bits':sorted(padding_bits),'constant_premises':constants,'shared_symbols':symbols,'exit_code':r.returncode,'success':'SAT proof finished - no model found: SUCCESS!' in r.stdout,'hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [*files,D/'cuts.json',D/'miter.v',D/'check.log']},'scope':'Actual er next-state unconditionally compared, hit next-state compared only under actual next er=1, all under guarded padding and named state relation. Current hit equality not proven when er=0. Write address/data compared only under pending write enable, read address under logical read valid. Six padding states independent arbitrary, guarded invariant explicitly required with separately bound binary base/preservation evidence. Other named current-state relations remain premises. Actual structural/native tag input functions and logical read-valid, read-address equality only when read-valid1 under explicit named paired current FF equality, merged aliases if any; zero constant-state premises. No init/preservation of those state relations, original four-state equivalence or Full admission.'};(D/'condition_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['coverage','constant_premises','independent_padding_bits','exit_code','success','scope']},indent=2));assert not constants;assert r.returncode==0 and out['success']
