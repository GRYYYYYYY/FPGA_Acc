"""Verify actual exported LUT masks and input routing against BLIF capture cone."""
import json,re,itertools,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];A=R/'experiments/full_ram_init_export_runtime_v8_2026-10-09/design.blif';V=R/'experiments/full_ibus_ready_preedge_trace_v1_2026-10-09/design.v';lines=A.read_text().splitlines();nodes={}
for i,line in enumerate(lines):
 if line.startswith('.names ') and line.split()[-1]=='b2692':
  rows=[]
  for t in lines[i+1:]:
   if t.startswith('.'):break
   if t.strip():rows.append(t.split())
  nodes['b2692']={'inputs':line.split()[1:-1],'rows':rows}
a={'actual_nodes':nodes};v=V.read_text();records=[]
for node in ['b2692']:
 pattern=r'LUT_K #\(\s*\.K\((\d+)\),\s*\.LUT_MASK\((\d+)\x27b([01]+)\)\s*\) \\lut_'+node+r'\s*\(\s*\.in\(\{([^}]+)\}\),\s*\.out\(\\lut_'+node+r'_output_0_0 \)\s*\);'
 match=re.search(pattern,v);assert match,node;k=int(match[1]);mask=match[3];assert len(mask)==2**k and int(match[2])==len(mask)
 terms=[t.strip() for t in match[4].split(',')];assert len(terms)==k;routes=[]
 for term in reversed(terms):
  if term in ["1'b0","1'b1"]:routes.append({'constant':term[-1]});continue
  rm=re.search(r'\.datain\(\\(?:lut|latch|\$_DFF_PP0_)_(\w+)_output_0_0 \),\s*\.dataout\('+re.escape(term)+r' \)',v);assert rm,(node,term);routes.append({'node':rm[1]})
 truth=a['actual_nodes'][node];assert {r['node'] for r in routes if 'node' in r}==set(truth['inputs'])
 checked=0
 for bits in itertools.product([0,1],repeat=len(truth['inputs'])):
  values=dict(zip(truth['inputs'],bits));addr=sum((int(r['constant']) if 'constant' in r else values[r['node']])<<lane for lane,r in enumerate(routes));actual=int(mask[-1-addr]);pol=int(truth['rows'][0][1]);hit=any(all(p=='-' or int(p)==b for p,b in zip(pattern,bits)) for pattern,_ in truth['rows']);expected=pol if hit else 1-pol;assert actual==expected
  checked+=1
 records.append({'node':node,'K':k,'mask':mask,'input_routes_lsb_first':routes,'checked_actual_rows':checked})
out={'records':records,'scope':'Exact actual export instance mask/input permutation/route correspondence for actual IBus ready LUT2692, not just BLIF formula. No four-state global events or complete replay admission.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [A,V]}}
D=R/'experiments/full_ibus_ready_export_lut_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'records':records},indent=2))
