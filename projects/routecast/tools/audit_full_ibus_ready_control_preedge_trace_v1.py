"""Full frozen replay fidelity and observed IBus ready controls."""
import json,re,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/full_ibus_ready_preedge_trace_v1_2026-10-09';D=R/'experiments/full_ibus_ready_control_preedge_trace_v1_2026-10-09'
st=json.loads((D/'stages.json').read_text());assert len(st)==3 and all(x['exit_code']==0 for x in st)
for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json']:assert (D/n).read_bytes()==(P/n).read_bytes()
assert (D/'tb.v').read_text().replace((D/'added_display.txt').read_text(),'')==(P/'tb.v').read_text()
log=(D/'control.log').read_text();parent=(P/'control.log').read_text();prefixes=set(re.findall(r'\$display\("([A-Z][A-Z0-9_]*)',(P/'tb.v').read_text()))
def records(t):return [line.strip() for line in t.splitlines() if any(re.search(r'\b'+p+r'\b',line) for p in prefixes)]
assert records(log)==records(parent);assert re.search(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*42370',log)
rows=[]
for line in log.splitlines():
 if 'IBUS_CONTROL_PREEDGE cycle=' not in line:continue
 row=dict(re.findall(r'(\w+)=\s*([01xXzZ]+)(?=\s|$)',line.replace('\\n',' ')));row['cycle']=int(re.search(r'cycle=\s*(\d+)',line)[1]);rows.append(row)
assert len(rows)==512 and [r['cycle'] for r in rows]==list(range(512))
A=R/'experiments/full_ibus_ready_control_export_luts_v1_2026-10-09/audit.json';import itertools
rec=next(r for r in json.loads(A.read_text())['records'] if r['node']=='new_n6085');parentrows=json.loads((P/'trace_audit.json').read_text())['rows']
for r,prior in zip(rows,parentrows):
 pins=r['control_pins'][::-1];assert pins==''.join(r[x['node']] for x in rec['input_routes_lsb_first'])
 values={rec['mask'][-1-sum(int(b)<<i for i,b in enumerate(bs))] for bs in itertools.product(*[['0','1'] if b in 'xz' else [b] for b in pins])};value=next(iter(values)) if len(values)==1 else 'x';assert value==prior['native_ready_pins'][::-1][1]
out={'cycles':512,'replay_fidelity':True,'mismatches':42370,'matched_control_mask_evaluations':512,'counts':{k:dict(collections.Counter(r[k] for r in rows)) for k in ['native_mmu_state','src_mmu_state','new_n6086','new_n6107','new_n6108','new_n6109','new_n6111']},'early_rows':rows[:7],'rows':rows,'scope':'Actual complete replay control6085 inputs/MMUstate preedges; allparentrecords and originalcomparison preserved. No global equivalence or allmismatch explanation.','hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['reference.v','design.v','tb.v','control.log','stages.json']}}
(D/'trace_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['rows','hashes']},indent=2))
