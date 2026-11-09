"""Bind raw exported node to actual eight BLIF selector capture/hold functions."""
import json,re,itertools,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];f=R/'experiments/full_ram_init_export_runtime_v8_2026-10-09/design.blif';v=R/'experiments/full_native_tag_access_path_trace_v1_2026-10-09/design.v';g=R/'experiments/full_native_ram_gates_v3_2026-10-09/gates.json';m=max(json.loads(g.read_text())['modules'].values(),key=lambda m:len(m['cells']));text=f.read_text();records=[]
for code in [768,256,384,836,772,833,834,835]:
 name='execute_CsrPlugin_csr_'+str(code);q=m['netnames'][name]['bits'][0];c=next(c for c in m['cells'].values() if c['connections'].get('Q')==[q]);d=c['connections']['D'][0];assert f'.latch b{d} b{q} re b254 2' in text
 match=re.search(r'^\.names ([^\n]+) b'+str(d)+r'\n([^.]*)',text,re.M);assert match
 inputs=match[1].split();rows=[line.split() for line in match[2].splitlines() if line.strip()];assert all(len(r)==2 and r[1]=='1' for r in rows)
 qi=inputs.index('b'+str(q));si=inputs.index('new_n5937')
 def value(bits):return int(any(all(p=='-' or int(p)==b for p,b in zip(pattern,bits)) for pattern,_ in rows))
 checked=0
 for bits in itertools.product([0,1],repeat=len(inputs)):
  if bits[si]==0:assert value(bits)==bits[qi]
  else:
   flipped=list(bits);flipped[qi]^=1;assert value(bits)==value(flipped)
  checked+=1
 records.append({'selector':name,'Q':q,'D':d,'inputs':inputs,'cubes':rows,'checked_binary_rows':checked})
assert 'wire \\lut_new_n5937_output_0_0 ;' in v.read_text()
out={'records':records,'conclusion':'For all8 actual BLIF selector D functions new_n5937=0 holds old Q; new_n5937=1 selects decode-dependent expression independent of old Q. This raw exported node is capture-high for these functions.','scope':'Binary actual BLIF truth tables and exported node existence. Does not prove four-state hold equivalence or equality to original !executeStuck, full decode expression, clock events or replay admission.','hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [f,v,g]}}
D=R/'experiments/full_native_csr_capture_node_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'selectors':len(records),'checked_rows':sum(r['checked_binary_rows'] for r in records),'conclusion':out['conclusion']}))
