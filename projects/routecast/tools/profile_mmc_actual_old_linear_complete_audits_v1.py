"""Instrument full independent audits of frozen development state; no gain claim."""
import cProfile,json,pstats,runpy,shutil,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
source=R/'experiments/ultraembedded_mmc_actual_old_linear_fallback_workflow_v11_2026-10-09/seed/model/mmc'
runner=R/'tools/run_shared_actual_old_linear_audits_v2.py'
admission=source/'shared_audit_receipt.json';proof=json.loads(admission.read_text())
assert proof['all_three_complete_audits_pass'] and proof['complete_audit_bodies_AST_preserved']
assert all(sha(p)==h for p,h in proof['bindings'].items())
D=R/'experiments/mmc_actual_old_linear_full_audit_profile_v1_2026-10-09'
D.mkdir();model=D/'model';model.mkdir()
bindings={**closure([Path(__file__),runner]),str(admission):sha(admission)}
# Exact copies; original model receipt bindings remain authenticated to frozen source.
for name in ['protocol.json','receipt.json','initial.json','floors.json','round0.json','round1.json','sketch.json']:
 old=source/name;new=model/name;shutil.copyfile(old,new)
 assert sha(old)==sha(new)
 bindings[str(old)]=sha(old);bindings[str(new)]=sha(new)
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Complete development MMC independent audit profiling of byte-identical frozen model copies. No new prediction or native labels; historical state read explicitly for diagnostics only. cProfile overhead included, no workflow or speedup claim. Original independent full body checks and fresh graph context retained.'),indent=2)+'\n')
prof=cProfile.Profile();sys.argv=[str(runner),str(model),'mmc'];begin=time.perf_counter()
prof.enable()
try:runpy.run_path(str(runner),run_name='__main__')
finally:
 prof.disable();prof.dump_stats(str(D/'full_audits.prof'))
elapsed=time.perf_counter()-begin
receipt=json.loads((model/'shared_audit_receipt.json').read_text())
assert receipt['all_three_complete_audits_pass']
assert all(sha(p)==h for p,h in receipt['bindings'].items())
assert all(sha(p)==h for p,h in bindings.items())
with (D/'profile_cumulative.txt').open('w') as f:pstats.Stats(prof,stream=f).strip_dirs().sort_stats('cumulative').print_stats(60)
with (D/'profile_self.txt').open('w') as f:pstats.Stats(prof,stream=f).strip_dirs().sort_stats('tottime').print_stats(60)
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,files={str(p):sha(p) for p in D.rglob('*') if p.is_file()},complete_instrumented_audits_pass=True,instrumented_seconds=elapsed,scope='Function hotspot diagnosis only; instrumented time not normal execution time or full workflow evidence.'),indent=2)+'\n')
print('Complete instrumented audits pass',elapsed,flush=True)
