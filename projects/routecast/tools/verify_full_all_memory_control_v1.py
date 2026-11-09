"""Conditional actual-cell memory interface equality at enabled reads/writes."""
import json,re,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_all_memory_control_sat_v1_2026-10-09';D.mkdir(exist_ok=True)
files=[E/'full_original_source_proc_state_v1_2026-10-09/source_proc.json',E/'full_ram_mapping_candidate_v1_2026-10-09/structural.json',E/'full_memory_read_port_binding_v1_2026-10-09/audit.json'];a,b,reads=[json.loads(f.read_text()) for f in files];a=next(iter(a['modules'].values()));b=next(iter(b['modules'].values()));sr={};mr={};effects=[];inventory=[]
for i,r in enumerate(reads['records']):
 prefix=f'r{i}';sr[prefix+'RA']=r['source_read_addr'];sr[prefix+'RE']=r['source_read_enable'];mr[prefix+'RA']=r['mapped_read_addr'];mr[prefix+'RE']=r['mapped_read_enable'];effects.extend([(prefix+'RE',None),(prefix+'RA',prefix+'RE')]);inventory.append({'prefix':prefix,'memory':r['memory'],'read_port':r['read_port']})
for i,name in enumerate(dict.fromkeys(r['memory'] for r in reads['records'])):
 w=[c for c in a['cells'].values() if c['type']=='$memwr_v2' and c['parameters']['MEMID'].lstrip('\\')==name];assert len(w)==1;w=w[0];assert len(set(w['connections']['EN']))==1;prefix=f'w{i}'
 for port,sourceport in [('WA','ADDR'),('WD','DATA'),('WE','EN')]:sr[prefix+port]=w['connections'][sourceport][:1] if port=='WE' else w['connections'][sourceport];mr[prefix+port]=b['netnames'][name+'.'+port]['bits']
 effects.extend([(prefix+'WE',None),(prefix+'WA',prefix+'WE'),(prefix+'WD',prefix+'WE')]);inventory.append({'prefix':prefix,'memory':name,'write_port':0})
def cut(m,roots,extra=()):
 drv={x:(n,c) for n,c in m['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for x in bs if isinstance(x,int)};used={};boundary=set();todo=list(roots)
 while todo:
  x=todo.pop()
  if not isinstance(x,int):continue
  if x in extra or x not in drv or re.match(r'^\$(?:[as]?dff|dlatch|mem)',drv[x][1]['type']):boundary.add(x);continue
  n,c=drv[x]
  if n in used:continue
  used[n]=c;todo.extend(x for p,bs in c['connections'].items() if c['port_directions'][p]=='input' for x in bs)
 return used,sorted(boundary)
sc,sb=cut(a,[x for v in sr.values() for x in v]);mc,mb=cut(b,[x for v in mr.values() for x in v]);wanted=set(sb);aliases={x:set() for x in sb}
for n,v in a['netnames'].items():
 if n not in b['netnames']:continue
 for i,x in enumerate(v['bits']):
  if x in wanted and i<len(b['netnames'][n]['bits']):aliases[x].add(b['netnames'][n]['bits'][i])
print("BAD_ALIASES",{x:sorted(v,key=str) for x,v in aliases.items() if len(v)!=1},flush=True);assert all(len(v)==1 for v in aliases.values());mapping={x:next(iter(v)) for x,v in aliases.items()};reverse={y:x for x,y in mapping.items() if isinstance(y,int)};print("REVERSE",len(reverse),len([v for v in mapping.values() if isinstance(v,int)]),flush=True);assert len(reverse)==len([v for v in mapping.values() if isinstance(v,int)]);mc,mb=cut(b,[x for v in mr.values() for x in v],set(reverse));print("UNMATCHED",sorted(set(mb)-set(reverse)),flush=True);assert set(mb)<=set(reverse);idx={x:i for i,x in enumerate(sb)};mods={};lines=[f'module miter(input [{len(sb)-1}:0] shared,output bad);']
for label,cells,leaves,roots in [('source',sc,sb,sr),('mapped',mc,mb,mr)]:
 ports={};con=[]
 for x in leaves:ports['i'+str(x)]={'direction':'input','bits':[x]};src=x if label=='source' else reverse[x];con.append(f'.i{x}(shared[{idx[src]}])')
 for n,bs in roots.items():ports[n]={'direction':'output','bits':bs};lines.append(f'wire [{len(bs)-1}:0] {label}_{n};');con.append(f'.{n}({label}_{n})')
 mods[label]={'attributes':{},'ports':ports,'cells':cells,'netnames':{}};lines.append(label+' u_'+label+'('+','.join(con)+');')
terms=[]
for n,en in effects:
 expr=f'(|(source_{n} ^ mapped_{n}))';terms.append(expr if en is None else f'(source_{en} && {expr})')
lines.append('assign bad='+' | '.join(terms)+'; endmodule');(D/'cuts.json').write_text(json.dumps({'creator':'actual cell subsets','modules':mods}));(D/'miter.v').write_text('\n'.join(lines)+'\n');constants={x:y for x,y in mapping.items() if isinstance(y,str)};assert all(y in ['0','1'] for y in constants.values());settings=' '.join(f'-set shared[{idx[x]}] {y}' for x,y in constants.items());(D/'check.ys').write_text(f'read_json cuts.json\nread_verilog miter.v\nhierarchy -check -top miter\nflatten\nopt\ncheck -assert\nsat {settings} -prove bad 0 -show-inputs -show-outputs -dump_json model.json\n');(D/'protocol.json').write_text(json.dumps({'inventory':inventory,'source_boundary':sb,'mapped_boundary':mb,'constant_premises':constants,'mapping':mapping,'source_cells':len(sc),'mapped_cells':len(mc),'scope':'Read/write enables always equal; address/data compared when corresponding operation enabled. Same binary shared-state premises and constant candidates; no inactive x-address equality demanded, memory initial/array relation unproved.'},indent=2)+'\n')
Y=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_Acc/projects/tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys')
with (D/'check.log').open('w') as log:
 try:code=subprocess.run([str(Y),'-s','check.ys'],cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=30).returncode
 except subprocess.TimeoutExpired:code='TIMEOUT'
t=(D/'check.log').read_text();out={'exit_code':code,'sat_success':code==0 and 'no model found: SUCCESS' in t,'counterexample':code==0 and 'model found: FAIL' in t,'read_ports':10,'write_ports':9,'functional_admission':False,'bindings':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),Y,*files,*D.iterdir()] if f.is_file()}};(D/'receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['exit_code','sat_success','counterexample','read_ports','write_ports']}))
