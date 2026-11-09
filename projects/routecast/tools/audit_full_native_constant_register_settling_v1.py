"""Structural clock-edge settling certificate; does not assert startup equality."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_native_constant_register_drivers_v1_2026-10-09/constant_audit.json';F=E/'full_ram_mapping_candidate_v1_2026-10-09/structural.json'
a=json.loads(P.read_text());m=max(json.loads(F.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{})))
rows=a['rows'];settled={};certs={}
for r in rows:
 if r['unconditional_capture_literal']:
  settled[r['q']]=1;certs[r['q']]={'kind':'direct_literal','edges':1}
for iteration in range(len(rows)):
 changed=False
 for r in rows:
  if r['q'] in settled or r['type']!='$dff' or r['data'] not in settled:continue
  upstream=next(x for x in rows if x['q']==r['data']);c=r['connections'];u=upstream['connections']
  if c['CLK']!=u['CLK'] or int(r['parameters']['CLK_POLARITY'],2)!=int(upstream['parameters']['CLK_POLARITY'],2) or r['literal']!=upstream['literal']:continue
  settled[r['q']]=settled[r['data']]+1;certs[r['q']]={'kind':'same_clock_pipeline','source_q':r['data'],'edges':settled[r['q']]};changed=True
 if not changed:break
drivers={b:(c,p,i) for c in m['cells'].values() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for i,b in enumerate(bs)}
remaining=[]
for r in rows:
 if r['q'] in settled:continue
 proof=None
 if r['data'] in drivers:
  c,p,i=drivers[r['data']]
  if c['type']=='$and' and p=='Y':
   for port in ['A','B']:
    bs=c['connections'][port]
    if i>=len(bs) and not int(c['parameters'][port+'_SIGNED'],2) and r['literal']=='0':proof={'kind':'unsigned_zero_extension_and_zero','zero_extended_operand':port,'output_lane':i,'update_requires_enable':r['type']=='$dffe'}
 remaining.append({'row':r,'data_constant_certificate':proof,'initial_value_proven':False})
out={'unconditional_settling_rows':len(settled),'edge_bound_counts':{str(n):sum(v==n for v in settled.values()) for n in sorted(set(settled.values()))},'certificates':{str(k):v for k,v in certs.items()},'remaining':remaining,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P,F]},'scope':'Actual same-clock dff chains settle after stated qualifying edges under simultaneous edge update semantics. No initial value or Full startup event ordering is established. Enabled constant D proves only enabled capture and preservation assuming Q already equals literal.'}
D=E/'full_native_constant_register_settling_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'settling_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'unconditional_settling_rows':len(settled),'edge_bound_counts':out['edge_bound_counts'],'remaining_rows':len(remaining),'remaining_with_constant_D_certificate':sum(bool(r['data_constant_certificate']) for r in remaining)},indent=2))
assert len(settled)==284 and len(remaining)==1 and remaining[0]['data_constant_certificate']
