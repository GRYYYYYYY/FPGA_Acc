"""Full frozen replay fidelity and observed IBus ready controls."""
import json,re,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/full_csr_counter_preedge_trace_v1_2026-10-09';D=R/'experiments/full_ibus_ready_preedge_trace_v1_2026-10-09'
st=json.loads((D/'stages.json').read_text());assert len(st)==3 and all(x['exit_code']==0 for x in st)
for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json']:assert (D/n).read_bytes()==(P/n).read_bytes()
assert (D/'tb.v').read_text().replace((D/'added_display.txt').read_text(),'')==(P/'tb.v').read_text()
log=(D/'control.log').read_text();parent=(P/'control.log').read_text();prefixes=set(re.findall(r'\$display\("([A-Z][A-Z0-9_]*)',(P/'tb.v').read_text()))
def records(t):return [line.strip() for line in t.splitlines() if any(re.search(r'\b'+p+r'\b',line) for p in prefixes)]
assert records(log)==records(parent);assert re.search(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*42370',log)
rows=[]
for line in log.splitlines():
 if 'IBUS_READY_PREEDGE cycle=' not in line:continue
 row=dict(re.findall(r'(\w+)=\s*([01xXzZ]+)(?=\s|$)',line.replace('\\n',' ')));row['cycle']=int(re.search(r'cycle=\s*(\d+)',line)[1]);rows.append(row)
assert len(rows)==512 and [r['cycle'] for r in rows]==list(range(512))
w=[r for r in rows if r['src_stuck']=='0' and r['src_issue'].lower()=='x'];diff=[r for r in rows if r['src_ready']!=r['native_ready']]
out={'replay_fidelity':True,'cycles':512,'mismatches':42370,'control_counts':{k:dict(collections.Counter(r[k] for r in rows)) for k in ['src_busy','src_stuck','src_issue','src_ready','src_bank_re','native_ready']},'source_semantic_witness_cycles':[r['cycle'] for r in w],'ready_difference_cycles':[r['cycle'] for r in diff],'first_witness':w[:1],'first_difference':diff[:1],'rows':rows,'scope':'Actual full replay preedge observations. Original stimulus/comparison/display sequence preserved. Source witness and actual native ready recorded separately, no assumed internal boundary equality or full mismatch explanation.','hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['reference.v','design.v','primitives.v','tb.v','frozen_bus_trace.json','control.log','stages.json']}}
(D/'trace_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['rows','hashes','source_semantic_witness_cycles','ready_difference_cycles']},indent=2))
