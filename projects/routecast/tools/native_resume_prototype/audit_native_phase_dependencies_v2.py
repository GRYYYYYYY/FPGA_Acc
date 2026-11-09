"""Printed native phase costs and packing/route synchronization dependencies."""
import sys,json,re
from pathlib import Path
from collections import Counter
from decimal import Decimal
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from source_binding import closure
R=Path(__file__).resolve().parents[2];s=R/'experiments/native_resume_shared_cold_adder_2026-10-07';o=R/'experiments/native_resume_phase_dependency_audit_v2_2026-10-07';o.mkdir(exist_ok=False);v=json.loads((s/'verified/verification.json').read_text());assert all(sha(p)==h for p,h in v['bindings'].items());inputs={str(s/'verified/verification.json'):sha(s/'verified/verification.json')};sources=closure([Path(__file__)]);rows=[];totals={'workflow':Counter(),'cold':Counter()};counts=Counter();fixes=Counter()
phases=('Loading Architecture Description','Building complex block graph','Load packing','Loading routing resource graph')
for i in range(1,10):
 for mode in ('workflow','cold'):
  b=R/f'experiments/native_resume_shared_cold_adder_step{i}_{mode}_2026-10-07';paths=['first/run.log','canonical/identity.log']
  paths+=['exchange_native/native.log','exchange_canonical/identity.log','exchange_canonical/reload.log'] if mode=='workflow' else ['canonical/reload.log']
  for relative in paths:
   p=b/relative;inputs[str(p)]=sha(p);body=p.read_text();timers=dict(re.findall(r'^#+ (.*?) took ([0-9.eE+-]+) seconds',body,re.M));selected={k:timers[k] for k in phases if k in timers};assert len(selected)==len(phases),(p,timers.keys());counts[mode]+=1
   for k,val in selected.items():totals[mode][k]+=Decimal(val)
   capture=relative.endswith('identity.log');matches=re.findall(r'Found (\d+) mismatches between routing and packing results',body);changes=re.findall(r'Fixed (\d+) routing traces due to mismatch',body);m=int(matches[-1]) if matches else None;f=int(changes[-1]) if changes else None
   if not capture:assert 'VPR succeeded' in body and m is not None and f is not None
   if relative.endswith('reload.log'):assert m==f==0
   if mode=='workflow' and relative=='exchange_native/native.log':fixes['feedback_mismatches']+=m;fixes['feedback_trace_fixups']+=f
   rows.append(dict(index=i,mode=mode,log=relative,native_identity_capture=capture,printed_phase_seconds=selected,packing_route_mismatches=m,trace_fixups=f))
# Actual hook target and synchronization implementation sites, read only.
shared=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';files=[R/'tools/native_net_identity_capture/hook.cpp',shared/'vpr/src/base/vpr_api.cpp']
for p in files:inputs[str(p)]=sha(p)
(o/'protocol.json').write_text(json.dumps(dict(inputs=inputs,sources=sources,scope='All logs from already native/physical-verified nine-step experiment. Printed phase durations rounded; selected phases reported individually, no summed end-to-end claim.'),indent=2)+'\n')
assert all(sha(p)==h for p,h in {**inputs,**sources}.items());result=dict(protocol_sha256=sha(o/'protocol.json'),rows=rows,core_native_process_counts=dict(counts),selected_phase_totals_seconds={mode:{k:str(v) for k,v in values.items()} for mode,values in totals.items()},feedback_sync_counters=dict(fixes),scope='45 workflow vs27 cold core native invocations, excluding external original-identity bootstrap/rebinding capture. Full end-to-end costs remain in shared-context sequence receipt. Identity capture intentionally fails at missing route after emitting table; not a native route success. Packing/route synchronization fixups demonstrate metadata changes; cannot skip final identity conversion or FULL/STA based on graph reuse.')
(o/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('core_native_process_counts','selected_phase_totals_seconds','feedback_sync_counters')},indent=2))
