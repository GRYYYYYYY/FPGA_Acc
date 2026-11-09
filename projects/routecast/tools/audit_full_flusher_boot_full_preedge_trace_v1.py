"""Full frozen replay fidelity and observed IBus ready controls."""
import json,re,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/full_ibus_fill_capture_preedge_trace_v1_2026-10-09';D=R/'experiments/full_flusher_boot_full_preedge_trace_v1_2026-10-09'
st=json.loads((D/'stages.json').read_text());assert len(st)==3 and all(x['exit_code']==0 for x in st)
for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json']:assert (D/n).read_bytes()==(P/n).read_bytes()
assert (D/'tb.v').read_text().replace((D/'added_display.txt').read_text(),'')==(P/'tb.v').read_text()
log=(D/'control.log').read_text();parent=(P/'control.log').read_text();prefixes=set(re.findall(r'\$display\("([A-Z][A-Z0-9_]*)',(P/'tb.v').read_text()))
def records(t):return [line.strip() for line in t.splitlines() if any(re.search(r'\b'+p+r'\b',line) for p in prefixes)]
assert records(log)==records(parent);assert re.search(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*42370',log)
rows=[]
for line in log.splitlines():
 if 'FLUSH_BOOT_PREEDGE cycle=' not in line:continue
 row=dict(re.findall(r'(\w+)=\s*([01xXzZ]+)(?=\s|$)',line.replace('\\n',' ')));row['cycle']=int(re.search(r'cycle=\s*(\d+)',line)[1]);rows.append(row)
assert len(rows)==512 and [r['cycle'] for r in rows]==list(range(512))
def inv(x):return {'0':'1','1':'0','x':'x'}[x]
def AND(a,b):return '0' if '0' in [a,b] else ('1' if a==b=='1' else 'x')
boot=[]
for r,nxt in zip(rows[:-1],rows[1:]):
 assert nxt['native_Q']==('0'*8 if r['reset']=='1' else r['native_D']),(r,nxt)
 if r['reset']=='1':expected='0'*8
 else:
  expected=r['src_counter']
  if r['src_increment']=='1':
   expected=format((int(expected,2)+1)%256,'08b')
   if r['src_singleLine']=='1':expected='1'+expected[1:]
  if r['src_start']=='1':expected=('0'+r['src_lineId']) if r['src_singleLine']=='1' else '0'*8
 assert nxt['src_counter']==expected,(r,nxt,expected)
 if r['native_start']=='1':
  assert r['native_D']=='0'+''.join(AND(inv(r['native_zero_instruction']),bit) for bit in r['native_lineId']);boot.append(r)
first=next((r for r in rows if r['src_counter']!=r['native_Q']),None)
out={'cycles':512,'replay_fidelity':True,'mismatches':42370,'native_capture_steps':511,'source_capture_steps':511,'first_counter_Q_difference':first,'boot_start_rows':boot,'early_rows':rows[:7],'rows':rows,'scope':'Actual fullcounterQ/D8/reset/lineId7/instruction5 preedges; unchanged originalfullcomparison. Correct reset override checked separately from D; knownbootstart1priority validated againstactualD. No global repair/admission or allmismatch causal attribution.','hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['reference.v','design.v','tb.v','control.log','stages.json']}}
(D/'trace_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['rows','hashes','boot_start_rows']},indent=2))
