"""Full frozen replay fidelity and observed IBus ready controls."""
import json,re,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/full_ibus_bank_history_preedge_trace_v1_2026-10-09';D=R/'experiments/full_ibus_write_history_preedge_trace_v1_2026-10-09'
st=json.loads((D/'stages.json').read_text());assert len(st)==3 and all(x['exit_code']==0 for x in st)
for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json']:assert (D/n).read_bytes()==(P/n).read_bytes()
assert (D/'tb.v').read_text().replace((D/'added_display.txt').read_text(),'')==(P/'tb.v').read_text()
log=(D/'control.log').read_text();parent=(P/'control.log').read_text();prefixes=set(re.findall(r'\$display\("([A-Z][A-Z0-9_]*)',(P/'tb.v').read_text()))
def records(t):return [line.strip() for line in t.splitlines() if any(re.search(r'\b'+p+r'\b',line) for p in prefixes)]
assert records(log)==records(parent);assert re.search(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*42370',log)
rows=[]
for line in log.splitlines():
 if 'IBUS_WRITE_PREEDGE cycle=' not in line:continue
 row=dict(re.findall(r'(\w+)=\s*([01xXzZ]+)(?=\s|$)',line.replace('\\n',' ')));row['cycle']=int(re.search(r'cycle=\s*(\d+)',line)[1]);rows.append(row)
assert len(rows)==512 and [r['cycle'] for r in rows]==list(range(512))
bank=json.loads((P/'trace_audit.json').read_text())['rows'];writes=[];diff=[]
for r,nxt,b in zip(rows[:-1],rows[1:],bank[:-1]):
 assert nxt['native_pa']==r['native_wa'],(r,nxt)
 assert nxt['native_pd']==b['src_wdata'],(r,nxt,b)
 if b['src_we']=='1':
  writes.append({'cycle':r['cycle'],'source_wa':b['src_wa'],'native_wa':r['native_wa'],'equal':b['src_wa']==r['native_wa']})
  if b['src_wa']!=r['native_wa']:diff.append(writes[-1])
out={'cycles':512,'replay_fidelity':True,'mismatches':42370,'matched_pending_address_steps':511,'matched_pending_payload_steps':511,'write_address_comparisons':writes,'write_address_differences':diff,'counts':{k:dict(collections.Counter(r[k] for r in rows)) for k in ['native_wa']},'early_rows':rows[:7],'rows':rows,'scope':'Actual full frozen replay pendingaddress=previousWA/payload=previousshareddata. Compare source/nativeWA onlyonactualsourcewrite cycles; equality/differences recorded without assumingmacrocontents or readoracle. Originalparentrecords preserved.','hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['reference.v','design.v','tb.v','control.log','stages.json']}}
(D/'trace_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'cycles':512,'pending_address_steps':511,'pending_data_steps':511,'write_comparisons':len(writes),'address_differences':len(diff),'first_difference':diff[:1]},indent=2))
