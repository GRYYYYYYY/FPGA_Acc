"""Inject wrong in-memory electrical scalar; complete frame audit must reject."""
import json,sys,subprocess,tempfile,runpy,linecache
from pathlib import Path
from fractions import Fraction
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
model=R/'experiments/xtea_actual_old_linear_native_handoff_v2_2026-10-09/model'
auditor=R/'tools/verify_resident_demand_frame_fraction_cache_v6.py'
if len(sys.argv)>1:
 mode=sys.argv[1];assert mode in ['initial','sketch','events']
 if mode=='events':auditor=R/'tools/verify_resident_events_actual_old_linear_fraction_cache_v11.py'
 import independent_fraction_arc_context_v2 as cache
 original=cache.arc_delay;calls=[0]
 def corrupted(classes,switches,node_class,switch_id):
  calls[0]+=1
  return original(classes,switches,node_class,switch_id)+Fraction(1,10**9)
 cache.arc_delay=corrupted
 with tempfile.TemporaryDirectory(prefix='routecast_fraction_corrupt_') as tmp:
  output=Path(tmp)/'verification.json';sys.argv=[str(auditor),str(model),'xtea' if mode=='events' else mode,str(output)]
  try:runpy.run_path(str(auditor),run_name='__main__')
  except AssertionError as error:
   tb=error.__traceback__
   while tb.tb_next is not None:tb=tb.tb_next
   assert Path(tb.tb_frame.f_code.co_filename).resolve()==auditor
   assert "rec['answer']['delay']" in linecache.getline(str(auditor),tb.tb_lineno)
   assert calls[0]>0 and not output.exists()
   print(json.dumps(dict(mode=mode,wrong_scalar_calls=calls[0],rejected_at_complete_delay_budget_check=True)),flush=True)
  else:raise AssertionError('corrupted scalar was accepted')
 sys.exit(0)
D=R/'experiments/fraction_cache_full_frame_event_corruption_v2_2026-10-10';D.mkdir()
bindings=closure([Path(__file__),auditor,R/'tools/verify_resident_events_actual_old_linear_fraction_cache_v11.py']);bindings.update({str(p):sha(p) for p in model.glob('*.json')})
rows=[]
for mode in ['initial','sketch','events']:
 p=subprocess.run([sys.executable,str(Path(__file__).resolve()),mode],cwd=R,capture_output=True,text=True,timeout=120)
 (D/(mode+'.log')).write_text(p.stdout+p.stderr)
 assert p.returncode==0,(mode,p.returncode,p.stderr)
 rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,files={str(p):sha(p) for p in D.glob('*.log')},complete_frame_and_event_audits_reject_wrong_cached_scalars=True,rows=rows,scope='Frozen complete XTEA development initial/final frame and committed-event rejection probes only. In-memory fault deliberately injected, sources/inputs unchanged. No MMC fallback-event corruption, arbitrary mutable mapping, full workflow gain or heldout claim.'),indent=2)+'\n')
print('PASS complete frame wrong-scalar rejection',rows,flush=True)
