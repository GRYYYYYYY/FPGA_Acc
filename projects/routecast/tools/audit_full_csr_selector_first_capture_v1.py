"""Bind real source first selector capture to existing unchanged full replay."""
import json,re,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];T=R/'experiments/full_csr_preedge_trace_v1_2026-10-09';S=R/'experiments/full_source_export_fixed_bus_replay_v19_2026-10-09';a=json.loads((T/'preedge_audit.json').read_text());rows=a['rows']
for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json']:assert (T/n).read_bytes()==(S/n).read_bytes()
tb=(T/'tb.v').read_text();assert tb.replace((T/'added_display.txt').read_text(),'')==(S/'tb.v').read_text();assert tb.index('$display("CSR_PREEDGE')<tb.index('clk=1;#1;compare;')
source=(T/'reference.v').read_text()
for name in ['when_Pipeline_l124_48']+['when_CsrPlugin_l1589'+suffix for suffix in ['', '_1','_2','_3','_4','_5','_6','_7']]:assert re.search(r'assign '+name+r' = \(! execute_arbitration_isStuck\);',source)
assert len(rows)==512 and a['mismatches']==42370
first=next(i for i,r in enumerate(rows) if r['pipe_en']=='1');assert first==132
assert all(r['pipe_en']=='0' and r['execute_valid']=='0' for r in rows[:first]);assert rows[first]['execute_valid']=='0'
assert rows[first]['select']=='x' and rows[first+1]['select']=='x'
assert all(r['trap']=='0' for r in rows)
out={'first_source_selector_capture_preedge_cycle':first,'before_capture_execute_valid_values':dict(collections.Counter(r['execute_valid'] for r in rows[:first+1])),'observed_csr834_selector_at_capture_and_next_preedge':[rows[first]['select'],rows[first+1]['select']],'source_capture_enable_values':dict(collections.Counter(r['pipe_en'] for r in rows)),'mismatches':a['mismatches'],'conclusion':'Actual original first selector capture occurs at cycle132, with executeValid0 through that preedge. Observed csr834 remains X next preedge: capture occurrence alone does not establish a known selector or paired decode data.','scope':'Existing source-only four-state preedge observation and exact shared enable definitions. Native first capture, all selector values, decode instruction equality and global admission unproved. Original frozen replay untouched.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [T/'reference.v',T/'tb.v',T/'control.log',T/'preedge_audit.json',T/'stages.json']}}
D=R/'experiments/full_csr_selector_first_capture_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='hashes'},indent=2))
