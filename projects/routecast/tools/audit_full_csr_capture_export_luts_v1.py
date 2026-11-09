"""Verify actual exported LUT masks and input routing against BLIF capture cone."""
import json,re,itertools,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];A=R/'experiments/full_csr_capture_access_dependency_v1_2026-10-09/audit.json';V=R/'experiments/full_csr_capture_operands_trace_v1_2026-10-09/design.v';a=json.loads(A.read_text());v=V.read_text();records=[]
for node in ['new_n5366','new_n5937']:
 pattern=r'LUT_K #\(\s*\.K\((\d+)\),\s*\.LUT_MASK\((\d+)\x27b([01]+)\)\s*\) \\lut_'+node+r'\s*\(\s*\.in\(\{([^}]+)\}\),\s*\.out\(\\lut_'+node+r'_output_0_0 \)\s*\);'
 match=re.search(pattern,v);assert match,node;k=int(match[1]);mask=match[3];assert len(mask)==2**k and int(match[2])==len(mask)
 terms=[t.strip() for t in match[4].split(',')];assert len(terms)==k;routes=[]
 for term in reversed(terms):
  if term in ["1'b0","1'b1"]:routes.append({'constant':term[-1]});continue
  rm=re.search(r'\.datain\(\\lut_(\w+)_output_0_0 \),\s*\.dataout\('+re.escape(term)+r' \)',v);assert rm,(node,term);routes.append({'node':rm[1]})
 truth=a['actual_nodes'][node];assert {r['node'] for r in routes if 'node' in r}==set(truth['inputs'])
 checked=0
 for bits in itertools.product([0,1],repeat=len(truth['inputs'])):
  values=dict(zip(truth['inputs'],bits));addr=sum((int(r['constant']) if 'constant' in r else values[r['node']])<<lane for lane,r in enumerate(routes));actual=int(mask[-1-addr]);pol=int(truth['rows'][0][1]);hit=any(all(p=='-' or int(p)==b for p,b in zip(pattern,bits)) for pattern,_ in truth['rows']);expected=pol if hit else 1-pol;assert actual==expected
  checked+=1
 records.append({'node':node,'K':k,'mask':mask,'input_routes_lsb_first':routes,'checked_actual_rows':checked})
out={'records':records,'scope':'Exact actual export instance mask/input permutation/route correspondence for two capture LUTs, not just BLIF formula. No four-state global events or complete replay admission.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [A,V]}}
D=R/'experiments/full_csr_capture_export_luts_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'records':records},indent=2))
