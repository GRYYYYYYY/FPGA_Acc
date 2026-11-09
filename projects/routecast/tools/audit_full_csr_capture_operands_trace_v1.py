"""Audit actual operand LUT evaluation after terminal unchanged full replay."""
import json,re,itertools,collections,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/full_csr_selector_native_trace_v1_2026-10-09';D=R/'experiments/full_csr_capture_operands_trace_v1_2026-10-09'
stages=json.loads((D/'stages.json').read_text());assert len(stages)==3 and all(s['exit_code']==0 for s in stages)
for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json']:assert (D/n).read_bytes()==(P/n).read_bytes()
assert (D/'tb.v').read_text().replace((D/'added_display.txt').read_text(),'')==(P/'tb.v').read_text()
log=(D/'control.log').read_text();parent=(P/'control.log').read_text();prefixes=set(re.findall(r'\$display\("([A-Z][A-Z0-9_]*)', (P/'tb.v').read_text()))
def records(text):return [line.strip() for line in text.splitlines() if any(re.search(r'\b'+prefix+r'\b',line) for prefix in prefixes)]
assert records(log)==records(parent),'Parent observation/input/full-compare records changed'
assert re.search(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*42370',log)
rows=[]
for line in log.splitlines():
 if 'CSR_CAPTURE_OPERANDS cycle=' not in line:continue
 row=dict(re.findall(r'(\w+)=\s*([01xXzZ]+)(?=\s|$)',line.replace('\\n',' ')));row['cycle']=int(re.search(r'cycle=\s*(\d+)',line)[1]);rows.append(row)
assert len(rows)==512 and [r['cycle'] for r in rows]==list(range(512))
logic=json.loads((R/'experiments/full_csr_capture_access_dependency_v1_2026-10-09/audit.json').read_text())['actual_nodes']
def eval_node(node,row):
 t=logic[node];bs=[['0','1'] if row[n].lower() in ['x','z'] else [row[n]] for n in t['inputs']];pol=int(t['rows'][0][1]);values=set()
 for bits in itertools.product(*bs):
  hit=any(all(p=='-' or p==b for p,b in zip(pattern,bits)) for pattern,_ in t['rows']);values.add(str(pol if hit else 1-pol))
 return next(iter(values)) if len(values)==1 else 'x'
parentrows=json.loads((P/'trace_audit.json').read_text())['rows']
for row,pr in zip(rows,parentrows):
 for node in ['new_n5366','new_n5937']:assert eval_node(node,row)==row[node],(node,row)
 assert row['new_n5937']==pr['native_capture_node'] and row['cycle']==pr['cycle']
out={'cycles':512,'mismatches':42370,'replay_fidelity':True,'matched_lut_evaluations':1024,'node_value_counts':{n:dict(collections.Counter(r[n] for r in rows)) for n in logic['new_n5937']['inputs']+['new_n5367','new_n5374','new_n5937']},'rows':rows,'scope':'Actual direct-node four-state observations and binary-completion LUT evaluation, with unchanged parent records/full comparison. Does not establish source/native binary reachability or all-mismatch cause.','hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['design.v','tb.v','control.log','stages.json']}}
(D/'trace_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['rows','hashes']},indent=2))
