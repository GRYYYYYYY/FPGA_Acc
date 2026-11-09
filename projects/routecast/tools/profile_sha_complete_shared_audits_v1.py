"""Isolated authenticated archival input clone, profile unchanged full audit bodies."""
import json,shutil,subprocess,sys
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];S=R/'experiments/sha1_actual_old_linear_expat_workflow_v1_2026-10-10/seed/model/sha1';D=R/'experiments/sha_complete_shared_audit_profile_v1_2026-10-10';assert not D.exists();D.mkdir();M=D/'model';M.mkdir();excluded={'initial_physical_verification.json','sketch_physical_verification.json','verification.json','shared_audit_receipt.json'};bindings={str(Path(__file__).resolve()):sha(Path(__file__))};copies=[]
for p in sorted(S.iterdir()):
 if not p.is_file() or p.name in excluded:continue
 q=M/p.name;shutil.copyfile(p,q);assert sha(q)==sha(p);bindings[str(p)]=sha(p);bindings[str(q)]=sha(q);copies.append(dict(source=str(p),clone=str(q),sha256=sha(p)))
assert (M/'initial.json').exists() and (M/'sketch.json').exists();runner=R/'tools/run_shared_actual_old_linear_direct_lattice_audits_v4.py';bindings[str(runner)]=sha(runner);cmd=[sys.executable,'-m','cProfile','-o',str(D/'profile.pstats'),str(runner),str(M),'sha1'];(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,copies=copies,command=cmd,scope='Frozen original model copied byte-for-byte, independent three full current-body audits re-executed in new output directory with fresh independent XML context. Historical input only for profiling, not new prospective model/fullworkflow gain. cProfile overhead included; original files never written; complete assertions retained.'),indent=2)+'\n')
with (D/'profile.log').open('w') as log:code=subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
out=dict(exit_code=code,scope='Diagnostic full-audit profiling only. No measured speedup or complete workflow conclusion.')
if code==0:
 p=M/'shared_audit_receipt.json';v=json.loads(p.read_text());assert v['all_three_complete_audits_pass'] and v['complete_audit_bodies_AST_preserved'] and v['fresh_independent_graph_context'];assert all(sha(k)==h for k,h in v['bindings'].items());out['full_three_audits_pass']=True;bindings[str(p)]=sha(p)
assert all(sha(k)==h for k,h in bindings.items());out['bindings']=bindings;(D/'receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='bindings'}))
