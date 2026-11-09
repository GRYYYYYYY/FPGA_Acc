"""Actual export mask/input routing audit for every visited debug-idle function."""
import json,re,itertools,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];A=R/'experiments/full_debug_idle_blif_unknown_v1_2026-10-09/audit.json';B=R/'experiments/full_ram_init_export_runtime_v8_2026-10-09/design.blif';V=R/'experiments/full_csr_counter_preedge_trace_v1_2026-10-09/design.v';a=json.loads(A.read_text());v=V.read_text();nodes={}
for mt in re.finditer(r'^\.names ([^\n]+)\n([^.]*)',B.read_text(),re.M):
 ns=mt[1].split();nodes[ns[-1]]={'inputs':ns[:-1],'rows':[r.split() for r in mt[2].splitlines() if r.strip() and not r.startswith('#')]}
routes={dest:src for src,dest in re.findall(r'\.datain\(\\([^ ]+) \),\s*\.dataout\(\\([^ ]+) \)',v)}
instances={n:(int(k),mask,terms) for k,width,mask,n,terms in re.findall(r'LUT_K #\(\s*\.K\((\d+)\),\s*\.LUT_MASK\((\d+)\x27b([01]+)\)\s*\) \\lut_(\w+)\s*\(\s*\.in\(\{([^}]+)\}\)',v)}
def logical(src):
 m=re.fullmatch(r'lut_(\w+)_output_0_0',src)
 if m:return m[1]
 m=re.fullmatch(r'(?:latch_|\$_DFF_[PN]+[01]?__)(b\d+)_output_0_0',src)
 if m:return m[1]
 if src.endswith('_output_0_0'):
  top=src[:-len('_output_0_0')];matches=[n for n,c in nodes.items() if c['inputs']==[top] and c['rows']==[['1','1']]]
  assert len(matches)==1,(src,matches);return matches[0]
 raise AssertionError(src)
records=[];missing=[]
for node in a['visited_nodes']:
 if node not in instances:missing.append(node);continue
 k,mask,terms=instances[node];terms=[t.strip() for t in terms.split(',')][::-1];pins=[];assert len(terms)==k and len(mask)==2**k
 for term in terms:
  if term in ["1'b0","1'b1"]:pins.append({'constant':term[-1]})
  else:assert term.startswith('\\');pins.append({'node':logical(routes[term[1:]])})
 truth=nodes[node];assert {p['node'] for p in pins if 'node' in p}==set(truth['inputs']),(node,pins,truth)
 checked=0
 for bs in itertools.product([0,1],repeat=len(truth['inputs'])):
  values=dict(zip(truth['inputs'],bs));addr=sum((int(p['constant']) if 'constant' in p else values[p['node']])<<i for i,p in enumerate(pins));pol=int(truth['rows'][0][1]);hit=any(all(p=='-' or int(p)==b for p,b in zip(pattern,bs)) for pattern,_ in truth['rows']);assert int(mask[-1-addr])==(pol if hit else 1-pol);checked+=1
 records.append({'node':node,'mask':mask,'pins_lsb_first':pins,'checked_rows':checked})
buffers=[]
for node in missing:
 c=nodes[node];assert len(c['inputs'])==1 and c['rows']==[['1','1']]
 top=c['inputs'][0];assert re.search(r'assign \\'+re.escape(top)+r'_output_0_0\s*=\s*\\'+re.escape(top)+r'\s*;',v)
 buffers.append({'blif_alias':node,'actual_top_port':top})
out={'verified_top_buffers':buffers,'checked_functions':len(records),'missing_export_instances':missing,'records':records,'scope':'Exact masks/input permutations/interconnects for visited exported debug-idle LUTs; missing instances retained explicitly. Real register/event binding and global admission separate.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [A,B,V]}}
D=R/'experiments/full_debug_idle_export_luts_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'checked_functions':len(records),'checked_rows':sum(r['checked_rows'] for r in records),'missing':missing}))
