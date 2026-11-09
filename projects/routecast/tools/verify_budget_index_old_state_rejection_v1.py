"""Real complete XTEA model rejects corrupt old ID state before ledger commit."""
import json,sys,subprocess,tempfile,linecache
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
import run_resident_actual_old_linear_budget_index_v12 as indexed
modelscript=Path(indexed.__file__).resolve()
endpoint=R/'experiments/freecores_native_demand_v1_2026-10-08/xtea/endpoints.json'
if len(sys.argv)>1:
 mode=sys.argv[1];assert mode in ['duplicate','missing']
 original=indexed.Search.search;captured={}
 def injected(self,source,sinks):
  answer=original(self,source,sinks);frame=sys._getframe(1)
  if not captured and 'round_index' in frame.f_locals:
   state=frame.f_locals;net=state['net'];old=state['records'][net]
   captured.update(frame=frame,ledger=dict(state['ledger']),epochs=state['epochs'].copy(),net=net)
   if mode=='duplicate':old.append(old[0])
   else:old.pop()
  return answer
 indexed.Search.search=injected
 with tempfile.TemporaryDirectory(prefix='routecast_budget_index_bad_old_') as tmp:
  output=Path(tmp)/'model'
  try:indexed.predict(endpoint,output)
  except AssertionError as error:
   tb=error.__traceback__
   while tb.tb_next:tb=tb.tb_next
   assert Path(tb.tb_frame.f_code.co_filename).resolve()==modelscript
   assert 'len(oldbyid)==len(old)==len(qs)' in linecache.getline(str(modelscript),tb.tb_lineno)
   assert captured and captured['frame'].f_locals['ledger']==captured['ledger']
   assert captured['frame'].f_locals['epochs']==captured['epochs']
   assert not (output/'receipt.json').exists() and not (output/'round0.json').exists()
   print(json.dumps(dict(mode=mode,old_identity_guard_rejected=True,ledger_epochs_unchanged_after_rejection=True,no_completed_feedback_or_success_receipt=True)),flush=True)
  else:raise AssertionError('corrupt old state accepted')
 sys.exit(0)
D=R/'experiments/budget_index_old_state_rejection_v1_2026-10-10';D.mkdir()
bindings={**closure([Path(__file__),modelscript]),str(endpoint):sha(endpoint)};rows=[]
for mode in ['duplicate','missing']:
 p=subprocess.run([sys.executable,str(Path(__file__).resolve()),mode],cwd=R,capture_output=True,text=True,timeout=120)
 (D/(mode+'.log')).write_text(p.stdout+p.stderr);assert p.returncode==0,(mode,p.stderr)
 rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,files={str(p):sha(p) for p in D.glob('*.log')},duplicate_and_missing_actual_old_ID_state_rejected_before_ledger_epoch_commit=True,rows=rows,scope='Real XTEA model fault injection at first feedback search. Only old records deliberately corrupted in memory; frozen endpoint/source files unchanged. Scratch search executes, ledger and epochs unchanged after rejection. No general concurrent memory atomicity, MMC proof or runtime gain claim.'),indent=2)+'\n')
print('PASS corrupt old identity rejection',rows,flush=True)
