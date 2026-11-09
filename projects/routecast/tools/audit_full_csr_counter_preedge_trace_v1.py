"""Audit actual sampled counter high D and next Q in unchanged full replay."""
import json,re,itertools,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/full_csr_capture_operands_trace_v1_2026-10-09';D=R/'experiments/full_csr_counter_preedge_trace_v1_2026-10-09'
stages=json.loads((D/'stages.json').read_text());assert len(stages)==3 and all(s['exit_code']==0 for s in stages)
for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json']:assert (D/n).read_bytes()==(P/n).read_bytes()
assert (D/'tb.v').read_text().replace((D/'added_display.txt').read_text(),'')==(P/'tb.v').read_text()
log=(D/'control.log').read_text();parent=(P/'control.log').read_text();prefixes=set(re.findall(r'\$display\("([A-Z][A-Z0-9_]*)',(P/'tb.v').read_text()))
def records(t):return [line.strip() for line in t.splitlines() if any(re.search(r'\b'+p+r'\b',line) for p in prefixes)]
assert records(log)==records(parent)
assert re.search(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*42370',log)
rows=[]
for line in log.splitlines():
 if 'CSR_COUNTER_PREEDGE cycle=' not in line:continue
 row=dict(re.findall(r'(\w+)=\s*([01xXzZ]+)(?=\s|$)',line.replace('\\n',' ')));row['cycle']=int(re.search(r'cycle=\s*(\d+)',line)[1]);rows.append(row)
assert len(rows)==512 and [r['cycle'] for r in rows]==list(range(512))
mask=json.loads((R/'experiments/full_source_export_data_flush_counter_trace_v16_2026-10-09/counter_high_pin_mapping.json').read_text())['mask']
for r in rows:
 pins=r['native_pins'][::-1];possibilities={mask[-1-sum(int(b)<<lane for lane,b in enumerate(bs))] for bs in itertools.product(*[['0','1'] if b.lower() in ['x','z'] else [b] for b in pins])};expected=next(iter(possibilities)) if len(possibilities)==1 else 'x';assert r['native_D']==expected
# Known deasserted reset and no extra positive clock edge between consecutive preedges.
for r,nextrow in zip(rows[3:-1],rows[4:]):assert r['native_D']==nextrow['native_Q'],(r,nextrow)
out={'replay_fidelity':True,'cycles':512,'mismatches':42370,'matched_preedge_D_evaluations':512,'matched_clock_capture_steps':508,'early_rows':rows[:7],'rows':rows,'scope':'Actual preedge D/nextpreedge Q with shared frozen input and unchanged complete comparison. Unknown controls retained; no global source/native equivalence or all-mismatch explanation.','hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['reference.v','design.v','tb.v','control.log','stages.json']}}
(D/'trace_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['rows','hashes']},indent=2))
