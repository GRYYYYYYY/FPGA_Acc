"""Actual-cell conditional next-state comparison; all missing premises explicit."""
import json,re,hashlib,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_external_output_state_closure_v1_2026-10-09';D=E/'full_new_output_dependency_register_step_v1_2026-10-09';D.mkdir(exist_ok=False)
files=[E/'full_original_source_proc_state_v1_2026-10-09/source_proc.json',E/'full_ram_mapping_candidate_v1_2026-10-09/structural.json',P/'mapping_candidates.json',P/'register_driver_pairs.json',E/'full_register_transfer_structure_all_outputs_v1_2026-10-09/audit.json']
s,m,c,pairs,proof=[json.loads(f.read_text()) for f in files];s=next(iter(s['modules'].values()));m=next(iter(m['modules'].values()));new_bits=set(json.loads((P/'extension_obligations.json').read_text())['extra_bits']);wanted={r['source_q'] for r in proof['records'] if not r['all_identical']} & new_bits;rows=[r for r in pairs['records'] if r['source_bit'] in wanted];boundary=[r['source_bit'] for r in c['records']];idx={b:i for i,b in enumerate(boundary)};reverse={r['mapped_candidates'][0]:r['source_bit'] for r in c['records'] if len(r['mapped_candidates'])==1 and isinstance(r['mapped_candidates'][0],int)};mods={};lines=[f'module miter(input [{len(boundary)-1}:0] shared,output bad);'];updates={}
for label,mod in [('source',s),('mapped',m)]:
 selected=[]; roots=[]
 for r in rows:
  cell=s['cells'][r['source_cell']] if label=='source' else m['cells'][r['mapped_driver']['cell']];lane=r['source_lane'] if label=='source' else r['mapped_driver']['lane'];ports={k:bs[lane if k in ['D','Q'] else 0] for k,bs in cell['connections'].items() if k!='CLK'};selected.append((cell,lane,ports));roots.extend(ports.values())
 roots=list(dict.fromkeys(roots));ri={b:i for i,b in enumerate(roots)};drivers={b:(n,v) for n,v in mod['cells'].items() for k,bs in v['connections'].items() if v['port_directions'][k]=='output' for b in bs if isinstance(b,int)};cutboundary=set(boundary) if label=='source' else set(reverse);used={};leaves=set();todo=list(roots)
 while todo:
  b=todo.pop()
  if not isinstance(b,int):continue
  if b in cutboundary:leaves.add(b);continue
  assert b in drivers,(label,'undriven',b)
  n,v=drivers[b];assert not re.match(r'^\$(?:[as]?dff|dlatch|mem)',v['type']),(label,'uncut',b)
  if n in used:continue
  used[n]=v;todo.extend(b for k,bs in v['connections'].items() if v['port_directions'][k]=='input' for b in bs)
 ports={'roots':{'direction':'output','bits':roots}};con=[f'.roots({label}_roots)'];lines.append(f'wire [{len(roots)-1}:0] {label}_roots;')
 for b in sorted(leaves):ports['i'+str(b)]={'direction':'input','bits':[b]};src=b if label=='source' else reverse[b];con.append(f'.i{b}(shared[{idx[src]}])')
 mods[label]={'attributes':{},'ports':ports,'cells':used,'netnames':{}};lines.append(label+' u_'+label+'('+','.join(con)+');');nxt=[]
 for cell,lane,pp in selected:
  expr=lambda k:f'{label}_roots[{ri[pp[k]]}]';params=cell['parameters'];value=expr('D')
  active=lambda k:expr(k) if int(params[k+'_POLARITY'],2) else '~'+expr(k)
  if 'SRST' in pp:
   val=params['SRST_VALUE'][::-1][lane]
   if cell['type']=='$sdffce':value=f'({active("EN")}?({active("SRST")}?1\'b{val}:{value}):{expr("Q")})'
   else:
    if 'EN' in pp:value=f'({active("EN")}?{value}:{expr("Q")})'
    value=f'({active("SRST")}?1\'b{val}:{value})'
  elif 'EN' in pp:value=f'({active("EN")}?{value}:{expr("Q")})'
  if 'ARST' in pp:value=f'({active("ARST")}?1\'b{params["ARST_VALUE"][::-1][lane]}:{value})'
  nxt.append(value)
 lines.append(f'wire [{len(nxt)-1}:0] {label}_next={{'+','.join(reversed(nxt))+'};');updates[label]={'root_count':len(roots),'comb_cells':len(used),'boundary_used':len(leaves)}
lines.append('assign bad=|(source_next ^ mapped_next); endmodule');(D/'cuts.json').write_text(json.dumps({'creator':'actual source and mapped combinational cells','modules':mods}));(D/'miter.v').write_text('\n'.join(lines)+'\n');(D/'check.ys').write_text(f'read_json cuts.json\nread_verilog miter.v\nhierarchy -check -top miter\nflatten\nopt\ncheck -assert\nsat -set shared[{idx[3149]}] 0 -prove bad 0 -show-inputs -show-outputs -dump_json model.json\n')
Y=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_Acc/projects/tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys');t=time.monotonic()
with (D/'check.log').open('w') as log:
 try:code=subprocess.run([str(Y),'-s','check.ys'],cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
 except subprocess.TimeoutExpired:code='TIMEOUT'
log=(D/'check.log').read_text();out={'exit_code':code,'sat_success':code==0 and 'no model found: SUCCESS' in log,'counterexample':code==0 and 'model found: FAIL' in log,'elapsed_seconds':time.monotonic()-t,'target_bits':len(rows),'target_source_q':[r['source_bit'] for r in rows],'cuts':updates,'scope':'Binary one-step actual next-state with enable/reset priorities; shared alias candidates and loader_killReg0 premises. Default Yosys undef semantics; no reset-reachable global relation, initial, memory, native-export or Full admission.','functional_admission':False,'bindings':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),Y,*files,*D.iterdir()] if f.is_file()}};(D/'receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['exit_code','sat_success','counterexample','elapsed_seconds','target_bits','cuts']}))
