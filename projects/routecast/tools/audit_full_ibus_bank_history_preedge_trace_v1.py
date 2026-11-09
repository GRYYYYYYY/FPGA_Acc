"""Full frozen replay bank history and observed enable/write captures."""
import json,re,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/full_ibus_ready_control_preedge_trace_v1_2026-10-09';D=R/'experiments/full_ibus_bank_history_preedge_trace_v1_2026-10-09'
st=json.loads((D/'stages.json').read_text());assert len(st)==3 and all(x['exit_code']==0 for x in st)
for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json']:assert (D/n).read_bytes()==(P/n).read_bytes()
assert (D/'tb.v').read_text().replace((D/'added_display.txt').read_text(),'')==(P/'tb.v').read_text()
log=(D/'control.log').read_text();parent=(P/'control.log').read_text();prefixes=set(re.findall(r'\$display\("([A-Z][A-Z0-9_]*)',(P/'tb.v').read_text()))
def records(t):return [line.strip() for line in t.splitlines() if any(re.search(r'\b'+p+r'\b',line) for p in prefixes)]
assert records(log)==records(parent);assert re.search(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*42370',log)
rows=[]
for line in log.splitlines():
 if 'IBUS_BANK_PREEDGE cycle=' not in line:continue
 row=dict(re.findall(r'(\w+)=\s*([01xXzZ]+)(?=\s|$)',line.replace('\\n',' ')));row['cycle']=int(re.search(r'cycle=\s*(\d+)',line)[1]);rows.append(row)
assert len(rows)==512 and [r['cycle'] for r in rows]==list(range(512))
ready=json.loads((R/'experiments/full_ibus_ready_preedge_trace_v1_2026-10-09/trace_audit.json').read_text())['rows'];memory={};checks=[];writes=[];holds=[]
for r,nxt,en in zip(rows[:-1],rows[1:],ready[:-1]):
 assert nxt['native_er']==en['native_ready'],(r,nxt,en)
 assert r['src_we'] in ['0','1'] and nxt['native_pw']==r['src_we'],(r,nxt)
 if en['src_bank_re']=='0':assert nxt['src_data']==r['src_data'];holds.append(r['cycle'])
 elif en['src_bank_re']=='1' and set(r['src_ra'])<={'0','1'}:
  addr=int(r['src_ra'],2)
  if addr in memory:
   assert nxt['src_data']==memory[addr],(r,nxt,memory[addr]);checks.append({'cycle':r['cycle'],'address':addr,'data':memory[addr]})
 if r['src_we']=='1' and set(r['src_wa'])<={'0','1'}:
  memory[int(r['src_wa'],2)]=r['src_wdata'];writes.append({'cycle':r['cycle'],'address':int(r['src_wa'],2),'data':r['src_wdata']})
 elif r['src_we']!='0':memory.clear() # conservative invalidation on unknown address/control
out={'cycles':512,'replay_fidelity':True,'mismatches':42370,'matched_er_capture_steps':511,'matched_pending_write_steps':511,'source_hold_checks':len(holds),'previously_written_read_checks':checks,'observed_source_writes':writes,'counts':{k:dict(collections.Counter(r[k] for r in rows)) for k in ['src_we','native_er','native_pw','native_hit']},'first_known_source_data':next((r for r in rows if set(r['src_data'])<={'0','1'}),None),'rows':rows,'scope':'Actual original frozen replay bank preedges. Known source writes tracked without assumed memory initialization; read oracle only for previously known writes, before sameedge write commit. Unknown write invalidates knowledge. Actual native er nextpreedge equals priorready. No native raw-array oracle or fullpayload equality claimed.','hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['reference.v','design.v','tb.v','control.log','stages.json']}}
(D/'trace_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['rows','hashes','observed_source_writes','previously_written_read_checks']},indent=2))
