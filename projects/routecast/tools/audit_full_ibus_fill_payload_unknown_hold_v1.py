"""Actual fill-payload LUT/register unknown persistence for capture0/X."""
import json,hashlib,itertools,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_ibus_fill_payload_unknown_hold_v1_2026-10-09';D.mkdir(exist_ok=True)
A=R/'experiments/full_ibus_fill_payload_export_luts_v1_2026-10-09/audit.json';V=R/'experiments/full_ibus_ready_preedge_trace_v1_2026-10-09/design.v';records=json.loads(A.read_text())['records'];v=V.read_text();trials=[]
for rec,q in zip(records,range(2294,2307,2)):
 routes=rec['input_routes_lsb_first'];payload=next(x['node'] for x in routes if 'node' in x and x['node'] not in ['b'+str(q),'b2692']);mask=rec['mask']
 for control,value in itertools.product('0x','01x'):
  vals={'b'+str(q):'x','b2692':control,payload:value};pins=[r['constant'] if 'constant' in r else vals[r['node']] for r in routes]
  possible={mask[-1-sum(int(b)<<i for i,b in enumerate(bits))] for bits in itertools.product(*[['0','1'] if b=='x' else [b] for b in pins])};assert possible=={'0','1'};trials.append({'Q':q,'capture':control,'payload':value,'D':'x'})
 assert re.search(r"DFF #\(\s*\.INITIAL_VALUE\(1'bx\)\s*\) \\latch_b"+str(q)+r'\s*\(',v)
 assert re.search(r'\.datain\(\\lut_'+rec['node']+r'_output_0_0 \),\s*\.dataout\(\\latch_b'+str(q)+r'_input_0_0 \)',v)
out={'trials':trials,'conclusion':'Each actual seven uninitialized fill-payload registers retains unknownD if currentQX and capture0/X, even if payload is known0/1. Only knownready1 can replace unknownoldQ. Actual mask/routes/initX/registerDroute checked.','scope':'Conditional local four-state consensus/primitive binding, actualready remains0/X in frozenfulltrace; directfill-payload traceallX separatelyverified; source/native inputaddress equality and complete admission remain separate.','hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [A,V]}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print('PASS42ternarytrials/7actualregisterbindings')
