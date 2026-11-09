"""Full frozen replay fidelity and observed IBus ready controls."""
import json,re,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/full_ibus_write_history_preedge_trace_v1_2026-10-09';D=R/'experiments/full_ibus_fill_capture_preedge_trace_v1_2026-10-09'
st=json.loads((D/'stages.json').read_text());assert len(st)==3 and all(x['exit_code']==0 for x in st)
for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json']:assert (D/n).read_bytes()==(P/n).read_bytes()
assert (D/'tb.v').read_text().replace((D/'added_display.txt').read_text(),'')==(P/'tb.v').read_text()
log=(D/'control.log').read_text();parent=(P/'control.log').read_text();prefixes=set(re.findall(r'\$display\("([A-Z][A-Z0-9_]*)',(P/'tb.v').read_text()))
def records(t):return [line.strip() for line in t.splitlines() if any(re.search(r'\b'+p+r'\b',line) for p in prefixes)]
assert records(log)==records(parent);assert re.search(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*42370',log)
rows=[]
for line in log.splitlines():
 if 'IBUS_FILL_PREEDGE cycle=' not in line:continue
 row=dict(re.findall(r'(\w+)=\s*([01xXzZ]+)(?=\s|$)',line.replace('\\n',' ')));row['cycle']=int(re.search(r'cycle=\s*(\d+)',line)[1]);rows.append(row)
assert len(rows)==512 and [r['cycle'] for r in rows]==list(range(512))
writes=json.loads((P/'trace_audit.json').read_text())['rows'];captures=[]
for r,nxt,nextwa in zip(rows[:-1],rows[1:],writes[1:]):
 assert r['src_fill'] in ['0','1']
 assert nxt['src_address']==(r['src_payload'] if r['src_fill']=='1' else r['src_address'])
 assert nextwa['native_wa'][:7]==r['native_D'],(r,nextwa)
 if r['src_fill']=='1':captures.append(r)
out={'cycles':512,'replay_fidelity':True,'mismatches':42370,'source_capture_hold_steps':511,'native_D_Q_steps':511,'counts':{k:dict(collections.Counter(r[k] for r in rows)) for k in ['src_fill','native_capture','native_payload','native_D']},'source_capture_rows':captures,'rows':rows,'scope':'Actual sourcefill/7payload/Q and nativeexportcapture6073/payload/D preedges with unchanged originalfullreplay. Actual nextQ matches D, no inventedinitialstate. Native6073 is actual finalcapture mux control, not assumed equal to sourcefill. No functionaladmission.','hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['reference.v','design.v','tb.v','control.log','stages.json']}}
(D/'trace_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['rows','hashes','source_capture_rows']},indent=2));print('first_source_capture',captures[:1])
