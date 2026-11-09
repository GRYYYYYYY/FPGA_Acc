"""Inventory all immediate consumers of guarded shared native states."""
import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_guarded_pending_native_capture_v1_2026-10-09/native_capture_audit.json';F=E/'full_native_ram_gates_v3_2026-10-09/gates.json'
a=json.loads(P.read_text());m=max(json.loads(F.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{})))
uses=collections.defaultdict(list)
for name,c in m['cells'].items():
 for port,bits in c['connections'].items():
  if c['port_directions'][port]!='input':continue
  for lane,bit in enumerate(bits):
   entry={'cell':name,'type':c['type'],'port':port,'lane':lane,'connections':c['connections']}
   if c['type']=='dual_port_ram' and port in ['addr1','data1']:entry['write_guard']=c['connections']['we1']
   uses[bit].append(entry)
rows=[]
for r in a['rows']:
 bit=r['native_q'];ports=[{'port':name,'direction':p['direction'],'lane':i} for name,p in m['ports'].items() for i,b in enumerate(p['bits']) if b==bit]
 rows.append({'native_q':bit,'immediate_consumers':uses[bit],'top_ports':ports,'ram_write_consumers':sum(u['type']=='dual_port_ram' and u['port'] in ['addr1','data1'] for u in uses[bit]),'other_consumers':sum(not(u['type']=='dual_port_ram' and u['port'] in ['addr1','data1']) for u in uses[bit])})
out={'rows':rows,'groups':len(rows),'ram_write_consumer_pins':sum(r['ram_write_consumers'] for r in rows),'other_consumer_pins':sum(r['other_consumers'] for r in rows),'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P,F]},'scope':'Complete immediate cell input and top-port consumer inventory only. Non-RAM consumers require downstream analysis; no assertion that all uses are write-enable masked. Tag source-side state must remain related unconditionally even when pending RAM-data equality is guarded.'}
D=E/'full_pending_native_consumers_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'consumer_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['rows','hashes']},indent=2))
